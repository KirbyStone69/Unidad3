#parte 1
    wc -l gdp_per_capita.csv 
    #191 gdp_per_capita.csv
    wc -l oecd_bli_2015.csv 
    #3293 oecd_bli_2015.csv


    #encabezados 
    head -n 1 gdp_per_capita.csv 
    head -n 1 oecd_bli_2015.csv 

    #los delimitadores
    # , \t  

#parte 2
    head -n 1 oecd_bli_2015.csv > oux.csv
    cat oecd_bli_2015.csv | grep SW_LIFS | grep TOT >> oux.csv 
    awk -F',' 'BEGIN{OFS=","} {print $2, $15}' oux.csv 
    #ya todo junto para usar las tuberias jeje
    awk -F',' 'NR==1 || ($3 ~ "SW_LIFS" && $7 ~ "TOT")' oecd_bli_2015.csv | cut -d',' -f2,15


    #parte 3 OFS para cambiar el delimitador, gsub una funcion para editar todo un patron de caracteres dentro de una columna
    awk -F'\t' 'BEGIN {OFS=","} {gsub(",","",$6)}{print $1,$6}' gdp_per_capita.csv

#parte 4
    #orden archivo1
    awk -F'\t' 'BEGIN {OFS=","} {gsub(",","",$6)}{print $1,$6}' gdp_per_capita.csv > oux.csv
    head -n 1 oux.csv > gdp_per_capita_filtrado.csv 
    tail -n +2 oux.csv | sort >> gdp_per_capita_filtrado.csv 
    #orden archivo2
    awk -F',' 'BEGIN{OFS=","} {print $2,$4}' oecd_bli_2015.csv > oux.csv
    head -n 1 oux.csv > oecd_bli_2015_ordenado.csv 
    tail -n +2 oux.csv | sort >> oecd_bli_2015_ordenado.csv 
    #pelandome con la parte de las comillas 
    cat oecd_bli_2015_ordenado.csv > oux.csv 
    tr -d '"' < oux.csv > oecd_bli_2015_ordenado.csv 
    #join final 
    cat << 'EOF' > merged_data.csv 
Country,Indicator,2015
EOF 
    join -1 1 -2 1 oecd_bli_2015_ordenado.csv gdp_per_capita_filtrado.csv | cat >> merged_data.csv

#parte5
    cut -d',' -f3 merged_data.csv > X.csv 
    cut -d',' -f2 merged_data.csv > Y.csv