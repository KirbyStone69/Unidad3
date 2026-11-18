"""EDA y clasificación de Iris, adaptados del notebook de Nourah (Apache 2.0).
Referencia: https://www.kaggle.com/code/engnoura2/simple-eda-decision-tree-classification
Ejecutar: .venv/bin/python analisis_iris.py

"""
# %% 1. Bibliotecas y rutas
from pathlib import Path
import json
import os

BASE = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(BASE / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')  # Guarda figuras incluso en equipos sin interfaz gráfica.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text

CARACTERISTICAS = ['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm']
SEMILLA = 1
PROFUNDIDAD_MAXIMA = 3
PORCENTAJE_PRUEBA = 0.30


def ejecutar():
    """Lee el CSV local y guarda tablas, métricas y gráficas en resultados/."""
    salida = BASE / 'resultados'
    salida.mkdir(exist_ok=True)
    sns.set_theme(style='whitegrid')
    registro = []

    def informar(titulo, contenido):
        texto = f'\n{titulo}\n{contenido}\n'
        print(texto)
        registro.append(texto)

    def guardar(nombre):
        plt.savefig(salida / nombre, dpi=160, bbox_inches='tight')
        plt.close('all')

    def paso(numero, titulo, explicacion):
        informar(f'PASO {numero:02d} | {titulo}', explicacion)

    informar('FUNDAMENTOS DE MACHINE LEARNING', 'Tradicional: datos + reglas -> resultados. ML: ejemplos etiquetados -> modelo.\nEste ejercicio: clasificación supervisada; y_hat = f(X).\nNo supervisado: busca grupos. Refuerzo: aprende mediante recompensas.')

    # %% 2. Materia prima: filas = flores; columnas = atributos y etiqueta.
    paso(1, 'CARGA DEL DATASET', 'Cada fila es una flor; cada columna, un atributo.')
    df = pd.read_csv(BASE / 'archive' / 'Iris.csv')
    informar('Tamaño de los datos', f'{df.shape[0]} instancias y {df.shape[1]} columnas.')
    informar('Primeras cinco filas', df.head().to_string(index=False))

    paso(2, 'REVISIÓN Y PREPARACIÓN DE LOS DATOS', 'Validamos columnas, tipos, faltantes, duplicados y medidas positivas.')
    requeridas = CARACTERISTICAS + ['Species']
    faltantes = set(requeridas) - set(df.columns)
    if faltantes:
        raise ValueError(f'Faltan columnas: {sorted(faltantes)}')
    if df[requeridas].isna().any().any():
        raise ValueError('Hay datos faltantes; revisa el CSV antes de entrenar.')
    if not all(pd.api.types.is_numeric_dtype(df[c]) for c in CARACTERISTICAS):
        raise ValueError('Las cuatro medidas deben ser numéricas.')
    if not np.isfinite(df[CARACTERISTICAS].to_numpy()).all() or (df[CARACTERISTICAS] <= 0).any().any():
        raise ValueError('Las medidas deben ser positivas y finitas.')

    # %% 3. Análisis exploratorio: estructura, calidad, clases y distribuciones.
    informar('Valores faltantes', df.isna().sum().to_string())
    informar('Duplicados de filas completas', int(df.duplicated().sum()))
    informar('Duplicados en medidas y especie (sin Id)', int(df.duplicated(subset=requeridas).sum()))
    informar('Decisión de preparación', 'Conservamos medidas repetidas; el árbol no requiere normalización.')

    paso(3, 'ANÁLISIS EXPLORATORIO (EDA)', 'Revisamos estadísticas, especies y distribuciones.')
    informar('Estadísticas descriptivas', df[CARACTERISTICAS].describe().to_string())
    informar('Distribución de especies', df['Species'].value_counts().to_string())
    df[CARACTERISTICAS].describe().to_csv(salida / 'estadisticas.csv')

    plt.figure(figsize=(8, 6))
    sns.heatmap(df[CARACTERISTICAS].corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Correlaciones entre características')
    guardar('01_correlaciones.png')

    df[CARACTERISTICAS].hist(figsize=(10, 7), bins=15)
    plt.suptitle('Distribución de las medidas (cm)')
    plt.tight_layout()
    guardar('02_histogramas.png')

    sns.pairplot(df, vars=CARACTERISTICAS, hue='Species', diag_kind='hist')
    guardar('03_relaciones.png')

    plt.figure(figsize=(8, 4))
    sns.countplot(data=df, y='Species', hue='Species', legend=False)
    plt.title('Número de flores por especie')
    guardar('04_especies.png')

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for columna, ax in zip(CARACTERISTICAS, axes.flat):
        sns.boxplot(data=df, x='Species', y=columna, hue='Species', legend=False, ax=ax)
        ax.tick_params(axis='x', rotation=15)
    fig.suptitle('Medidas por especie (cm)')
    fig.tight_layout()
    guardar('05_medidas_por_especie.png')

    # %% 4. Aprendizaje supervisado: f(X) predice y = especie.
    # Id identifica una fila; no es una medida de la flor y se excluye.
    paso(4, 'CARACTERÍSTICAS X Y ETIQUETA y', 'X: cuatro medidas (cm). y: Species. Se excluye Id.')
    X, y = df[CARACTERISTICAS], df['Species']
    informar('Forma de X e y', f'X: {X.shape}; y: {y.shape}.')
    informar('Características utilizadas', ', '.join(CARACTERISTICAS))
    informar('Un ejemplo etiquetado', f'X[0] = {X.iloc[0].tolist()} -> y[0] = {y.iloc[0]}')
    # %% 5. Partición estratificada: mantiene la proporción de especies.
    paso(5, 'PARTICIÓN DE LOS DATOS', '70 % entrenamiento y 30 % prueba, con estratificación y semilla fija.')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=PORCENTAJE_PRUEBA, random_state=SEMILLA, stratify=y)
    particiones = df[['Id', 'Species']].copy()
    particiones['particion'] = 'entrenamiento'
    particiones.loc[X_test.index, 'particion'] = 'prueba'
    particiones.to_csv(salida / 'particiones.csv', index=False)
    informar('Partición de datos', f'Entrenamiento: {len(X_train)}; prueba: {len(X_test)}')
    coincidencias = len(X_test.merge(X_train.drop_duplicates(), on=CARACTERISTICAS))
    informar('Flores de prueba con medidas iguales a alguna de entrenamiento', coincidencias)

    # %% 6. Modelo del ejemplo: entropía y profundidad máxima 3.
    paso(6, 'ENTRENAMIENTO DEL MODELO', 'El árbol aprende con fit(X_train, y_train).')
    modelo = DecisionTreeClassifier(criterion='entropy', max_depth=PROFUNDIDAD_MAXIMA, random_state=SEMILLA)
    modelo.fit(X_train, y_train)

    paso(7, 'PREDICCIÓN Y EVALUACIÓN EN PRUEBA', 'Comparamos predicciones con etiquetas reales: exactitud, precisión, recall y F1.')
    predicciones = modelo.predict(X_test)
    clases = modelo.classes_.tolist()
    exactitud = accuracy_score(y_test, predicciones)
    informe = classification_report(y_test, predicciones, labels=clases, zero_division=0)
    base = DummyClassifier(strategy='most_frequent').fit(X_train, y_train)
    informar('Exactitud en entrenamiento', f'{modelo.score(X_train, y_train):.2%}')
    informar('Exactitud en prueba', f'{exactitud:.2%}')
    informar('Referencia: predecir siempre la especie mayoritaria', f'{base.score(X_test, y_test):.2%}')
    informar('Reporte de clasificación', informe)
    metricas = {
        'filas': len(df), 'caracteristicas': CARACTERISTICAS,
        'entrenamiento': len(X_train), 'prueba': len(X_test), 'semilla': SEMILLA,
        'accuracy_train': modelo.score(X_train, y_train), 'accuracy_test': exactitud,
        'accuracy_referencia': base.score(X_test, y_test),
        'reporte': classification_report(y_test, predicciones, labels=clases,
                                         output_dict=True, zero_division=0)}
    (salida / 'metricas.json').write_text(json.dumps(metricas, indent=2, ensure_ascii=False))
    resultados = X_test.copy()
    resultados.insert(0, 'Id', df.loc[X_test.index, 'Id'])
    resultados['especie_real'] = y_test
    resultados['especie_predicha'] = predicciones
    resultados.to_csv(salida / 'predicciones.csv', index=False)

    ConfusionMatrixDisplay.from_predictions(y_test, predicciones, labels=clases,
                                           cmap='Blues', xticks_rotation=20)
    plt.title('Matriz de confusión — conjunto de prueba')
    guardar('06_matriz_confusion.png')

    # %% 7. Visualización del árbol e importancia de las características.
    paso(8, 'INTERPRETACIÓN DE LAS REGLAS', 'Guardamos el árbol, sus reglas y la importancia de las características.')
    plt.figure(figsize=(18, 9))
    plot_tree(modelo, feature_names=CARACTERISTICAS, class_names=clases,
              filled=True, rounded=True, fontsize=10)
    plt.title('Árbol de decisión: clasificación de Iris')
    guardar('07_arbol_decision.png')
    reglas = export_text(modelo, feature_names=CARACTERISTICAS)
    (salida / 'reglas_arbol.txt').write_text(reglas)
    importancia = pd.Series(modelo.feature_importances_, index=CARACTERISTICAS).sort_values()
    importancia.plot.barh(figsize=(8, 4))
    plt.xlabel('Importancia en este árbol')
    plt.title('Características utilizadas por el modelo')
    guardar('08_importancia.png')

    # %% 8. Generalización: contraste de complejidad usando SOLO entrenamiento.
    # La prueba no se usa para escoger profundidad. CV = validación cruzada.
    paso(9, 'GENERALIZACIÓN: SUBAJUSTE, SOBREAJUSTE Y EQUILIBRIO', 'Comparamos profundidades con validación cruzada solo en entrenamiento.\nSubajuste: poca complejidad. Sobreajuste: buen entrenamiento, peor validación.')
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    comparacion = []
    for profundidad in [1, 2, 3, 4, 5, None]:
        candidato = DecisionTreeClassifier(criterion='entropy', max_depth=profundidad,
                                           random_state=SEMILLA)
        scores = cross_validate(candidato, X_train, y_train, cv=cv,
                                scoring='accuracy', return_train_score=True)
        comparacion.append({'profundidad': str(profundidad) if profundidad else 'Sin límite',
                            'exactitud_entrenamiento': scores['train_score'].mean(),
                            'exactitud_validacion': scores['test_score'].mean(),
                            'desviacion_validacion': scores['test_score'].std()})
    tabla = pd.DataFrame(comparacion)
    tabla.to_csv(salida / 'comparacion_profundidad.csv', index=False)
    informar('Diagnóstico por profundidad (validación cruzada en entrenamiento)', tabla.to_string(index=False))
    plt.figure(figsize=(9, 5))
    plt.plot(tabla['profundidad'], tabla['exactitud_entrenamiento'], 'o-', label='Entrenamiento CV')
    plt.errorbar(tabla['profundidad'], tabla['exactitud_validacion'],
                 yerr=tabla['desviacion_validacion'], fmt='o-', label='Validación CV ± desviación')
    plt.xlabel('Profundidad máxima')
    plt.ylabel('Exactitud')
    plt.title('Complejidad y generalización')
    plt.legend()
    guardar('09_generalizacion.png')
    simple = tabla.iloc[0]
    profundo = tabla.iloc[-1]
    informar('Comparación',
             f'Profundidad 1: validación {simple.exactitud_validacion:.2%}. '
             f'Sin límite: validación {profundo.exactitud_validacion:.2%}.')
    informar('Interpretación', 'Ajusta la complejidad con validación, sin usar prueba para elegir parámetros.\nSi las medidas repetidas son la misma flor, agrúpalas antes de partir.')

    paso(10, 'USO DEL MODELO Y CONSERVACIÓN DE RESULTADOS', 'Predecimos una especie y guardamos los resultados.')
    ejemplo = pd.DataFrame([[5.1, 3.5, 1.4, 0.2]], columns=CARACTERISTICAS)
    informar('Ejemplo de f(X)', f'{ejemplo.iloc[0].tolist()} -> {modelo.predict(ejemplo)[0]}')
    informar('Ecosistema utilizado', 'pandas/NumPy: datos; seaborn/Matplotlib: gráficas; scikit-learn: modelo.')
    informar('Ejercicio para practicar', 'Compara profundidad 1 con 3: ¿cómo cambian entrenamiento y validación?')
    informar('Archivos generados', str(salida))
    (salida / 'reporte.txt').write_text(''.join(registro), encoding='utf-8')
    return metricas


if __name__ == '__main__':
    ejecutar()
