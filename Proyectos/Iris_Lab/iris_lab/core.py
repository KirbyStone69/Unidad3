"""Motor de análisis independiente de la interfaz gráfica.

Adaptación del ejemplo de Nourah (Apache 2.0):
https://www.kaggle.com/code/engnoura2/simple-eda-decision-tree-classification
"""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
import hashlib
import json
import zipfile

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

FEATURES = ['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm']
NAMES = ['Largo del sépalo', 'Ancho del sépalo', 'Largo del pétalo', 'Ancho del pétalo']
SPECIES = ['Iris-setosa', 'Iris-versicolor', 'Iris-virginica']
COLORS = ['#7860dc', '#239e93', '#d99a3a']
BASE = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    depth: int = 3
    test_percent: int = 30
    criterion: str = 'entropy'
    seed: int = 1


@dataclass
class Result:
    settings: Settings
    model: DecisionTreeClassifier
    train_indices: list
    test_indices: list
    predictions: pd.DataFrame
    accuracy: float
    train_accuracy: float
    macro_f1: float
    baseline: float
    confusion: np.ndarray
    report: pd.DataFrame
    validation: pd.DataFrame
    overlap: int


def validate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Valida el esquema Iris y devuelve datos limpios sin modificar la entrada."""
    missing = set(FEATURES + ['Species']) - set(df.columns)
    if missing:
        raise ValueError(f'Faltan columnas: {", ".join(sorted(missing))}.')
    frame = df.copy().reset_index(drop=True)
    try:
        frame[FEATURES] = frame[FEATURES].apply(pd.to_numeric, errors='raise')
    except (ValueError, TypeError) as exc:
        raise ValueError('Las cuatro medidas deben ser numéricas, en centímetros.') from exc
    if not np.isfinite(frame[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError('Las medidas contienen valores vacíos o infinitos.')
    if (frame[FEATURES] <= 0).any().any():
        raise ValueError('Las medidas deben ser mayores que cero.')
    if frame.Species.isna().any() or not frame.Species.isin(SPECIES).all():
        raise ValueError('Cada especie debe ser Iris-setosa, Iris-versicolor o Iris-virginica.')
    counts = frame.Species.value_counts()
    if len(counts) != 3 or counts.min() < 5:
        raise ValueError('Se necesitan las tres especies, con al menos 5 flores por especie.')
    if 'Id' not in frame:
        frame.insert(0, 'Id', np.arange(1, len(frame) + 1))
    return frame[['Id'] + FEATURES + ['Species']]


def load_dataset(path: Path | str) -> pd.DataFrame:
    return validate_dataset(pd.read_csv(path))


def train(df: pd.DataFrame, settings: Settings,
          progress: Callable[[int, str], None] | None = None) -> Result:
    """Entrena un árbol y realiza CV solo dentro de entrenamiento."""
    if not 1 <= settings.depth <= 12:
        raise ValueError('La profundidad debe estar entre 1 y 12.')
    if not 15 <= settings.test_percent <= 40:
        raise ValueError('El porcentaje de prueba debe estar entre 15 y 40.')
    if settings.criterion not in ('entropy', 'gini'):
        raise ValueError('El criterio debe ser entropy o gini.')
    if not 0 <= settings.seed <= 99999:
        raise ValueError('La semilla debe estar entre 0 y 99999.')
    emit = progress or (lambda *_: None)
    frame = validate_dataset(df)
    emit(10, 'Separando entrenamiento y prueba…')
    X, y = frame[FEATURES], frame.Species
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=settings.test_percent / 100,
        random_state=settings.seed, stratify=y)
    emit(25, 'Aprendiendo las reglas del árbol…')
    model = DecisionTreeClassifier(criterion=settings.criterion, max_depth=settings.depth,
                                   random_state=settings.seed).fit(Xtr, ytr)
    predicted = model.predict(Xte)
    predictions = frame.loc[Xte.index].copy()
    predictions = predictions.rename(columns={'Species': 'especie_real'})
    predictions['especie_predicha'] = predicted
    predictions['acierto'] = predictions.especie_real == predictions.especie_predicha
    baseline = DummyClassifier(strategy='most_frequent').fit(Xtr, ytr).score(Xte, yte)
    report = classification_report(yte, predicted, labels=SPECIES,
                                   output_dict=True, zero_division=0)
    report_frame = pd.DataFrame({s: report[s] for s in SPECIES}).T
    report_frame.index.name = 'Especie'
    report_frame = report_frame.reset_index()
    folds = min(5, int(ytr.value_counts().min()))
    if folds < 2:
        raise ValueError('Faltan flores por clase en entrenamiento para validar el modelo.')
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=settings.seed)
    rows = []
    depths = [1, 2, 3, 4, 5, None]
    for i, depth in enumerate(depths):
        emit(35 + i * 10, f'Validando profundidad {depth or "sin límite"}…')
        candidate = DecisionTreeClassifier(criterion=settings.criterion, max_depth=depth,
                                           random_state=settings.seed)
        scores = cross_validate(candidate, Xtr, ytr, cv=cv, return_train_score=True,
                                scoring='accuracy', n_jobs=1)
        rows.append({'profundidad': str(depth) if depth else 'Sin límite',
                     'entrenamiento': float(scores['train_score'].mean()),
                     'validacion': float(scores['test_score'].mean()),
                     'desviacion': float(scores['test_score'].std())})
    overlap = int(len(Xte.merge(Xtr.drop_duplicates(), on=FEATURES)))
    emit(100, 'Experimento listo')
    return Result(settings, model, Xtr.index.tolist(), Xte.index.tolist(), predictions,
                  float(accuracy_score(yte, predicted)), float(model.score(Xtr, ytr)),
                  float(f1_score(yte, predicted, average='macro')), float(baseline),
                  confusion_matrix(yte, predicted, labels=SPECIES), report_frame,
                  pd.DataFrame(rows), overlap)


def predict(result: Result, values: list[float]) -> tuple[str, dict]:
    measurements = np.asarray(values, dtype=float)
    if measurements.shape != (4,) or not np.isfinite(measurements).all() or (measurements <= 0).any():
        raise ValueError('Introduce cuatro medidas positivas y finitas en centímetros.')
    row = pd.DataFrame([measurements], columns=FEATURES)
    label = str(result.model.predict(row)[0])
    probabilities = dict(zip(result.model.classes_, map(float, result.model.predict_proba(row)[0])))
    return label, probabilities


def export_experiment(path: Path | str, df: pd.DataFrame, result: Result) -> None:
    """Exporta los datos y resultados del modelo, sin serialización ejecutable."""
    content = df.to_csv(index=False)
    summary = {'settings': asdict(result.settings), 'accuracy_test': result.accuracy,
               'accuracy_train': result.train_accuracy, 'macro_f1': result.macro_f1,
               'baseline': result.baseline, 'train_indices': result.train_indices,
               'test_indices': result.test_indices, 'matching_test_measurements': result.overlap,
               'dataset_sha256': hashlib.sha256(content.encode()).hexdigest()}
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('dataset.csv', content)
        archive.writestr('metricas.json', json.dumps(summary, indent=2, ensure_ascii=False))
        archive.writestr('predicciones.csv', result.predictions.to_csv(index=False))
        archive.writestr('validacion.csv', result.validation.to_csv(index=False))
        archive.writestr('reporte_clasificacion.csv', result.report.to_csv(index=False))
        archive.writestr('reglas_arbol.txt', export_text(result.model, feature_names=FEATURES))
