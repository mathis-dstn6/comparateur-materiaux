import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la structure de la page web
st.set_page_config(page_title="Éco-Conception Métallurgique Pro", layout="wide")

st.title("🌱 Outil d'Éco-Conception Métallurgique Professionnel")
st.write("Le couteau suisse de l'ingénieur pour la substitution éco-responsable des métaux.")

# --- 1. CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data
def charger_donnees():
    # Lecture du fichier de 500 lignes généré
    df = pd.read_csv('alliages_metalliques_4_1.csv', sep=';')
        
    colonnes_a_nettoyer = [
        'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
        'Empreinte_CO2', 'Prix_euro_kg', 'Temp_Fusion_C', 
        'Conductivite_Thermique_W_mK', 'Recyclabilite_pct'
    ]
    for col in colonnes_a_nettoyer:
        if col in df.columns:
            df[col] = df[col].replace(0, 1e-6)
            
    # --- CALCUL DES INDICES D'ASHBY (Propriétés spécifiques) ---
    # Indice 1 : Traction légère (Limite élastique / Densité)
    df['Indice_Traction'] = df['Limite_Elastique_MPa'] / df['Densite']
    # Indice 2 : Flexion légère (Racine de Limite élastique / Densité)
    df['Indice_Flexion'] = np.sqrt(df['Limite_Elastique_MPa']) / df['Densite']
    
    return df

df_initial = charger_donnees()

colonnes_affichage = [
    'Nom', 'Famille', 'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
    'Temp_Fusion_C', 'Conductivite_Thermique_W_mK', 
    'Empreinte_CO2', 'Recyclabilite_pct', 'Prix_euro_kg'
]

# --- 2. CRÉATION DES DEUX ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Remplacement & Éco-Sélection", "📐 Cahier des Charges & Ashby"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE + SUGGESTION ---
with tab1:
    st.header("🔄 Assistant de Substitution Intelligent")
    st.write("Filtrez par famille métallurgique pour cibler un jumeau numérique performant.")
    
    # Filtre par famille pour simplifier la recherche parmi les 500 alliages
    familles_disponibles = ['Toutes'] + sorted(df_initial['Famille'].unique().tolist())
    famille_choisie = st.selectbox("Filtrer la liste par famille métallurgique :", familles_disponibles)
    
    if famille_choisie != 'Toutes':
        df_recherche = df_initial[df_initial['Famille'] == famille_choisie]
    else:
        df_recherche = df_initial
        
    col_sel, col_param = st.columns([1, 1])
    with col_sel:
        liste_materiaux = df_recherche['Nom'].tolist()
        materiau_ref = st.selectbox("Sélectionnez le matériau actuel à remplacer :", liste_materiaux)
        row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
        
    with col_param:
        objectif = st.radio(
            "Quel est votre objectif prioritaire pour l'alternative ?",
            ["Réduire l'empreinte CO₂", "Réduire le prix (€/kg)"]
        )
    
    st.markdown(f"#### 📊 Propriétés actuelles de : **{materiau_ref}** ({row_ref['Famille']})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Limite Élastique", f"{row_ref['Limite_Elastique_MPa']} MPa")
    c2.metric("Temp. de Fusion", f"{row_ref['Temp_Fusion_C']} °C")
    c3.metric("Empreinte CO₂", f"{row_ref['Empreinte_CO2']} kg/kg")
    c4.metric("Prix", f"{row_ref['Prix_euro_kg']} €/kg")
    
    st.write("---")
    st.subheader("💡 Assistant de Substitution Avancé")
    st.write("Cochez les critères requis et ajustez la tolérance (perte maximale acceptable) :")
    
    c_check1, c_check2, c_check3 = st.columns(3)
    with c_check1:
        keep_mecha = st.checkbox("Conserver la résistance mécanique", value=True)
        tol_mecha = st.slider("Tolérance Limite Élastique (%)", 0, 50, 20, disabled=not keep_mecha)
    with c_check2:
        keep_thermal = st.checkbox("Conserver la tenue thermique", value=False)
        tol_thermal = st.slider("Tolérance Température de Fusion (%)", 0, 50, 20, disabled=not keep_thermal)
    with c_check3:
        keep_stiff = st.checkbox("Conserver la rigidité", value=False)
        tol_stiff = st.slider("Tolérance Module de Young (%)", 0, 50, 20, disabled=not keep_stiff)

    df_alt = df_initial[df_initial['Nom'] != materiau_ref].copy()
    if keep_mecha:
        df_alt = df_alt[df_alt['Limite_Elastique_MPa'] >= row_ref['Limite_Elastique_MPa'] * (1 - (tol_mecha / 100))]
    if keep_thermal:
        df_alt = df_alt[df_alt['Temp_Fusion_C'] >= row_ref['Temp_Fusion_C'] * (1 - (tol_thermal / 100))]
    if keep_stiff:
        df_alt = df_alt[df_alt['Module_Young_GPa'] >= row_ref['Module_Young_GPa'] * (1 - (tol_stiff / 100))]
        
    if objectif == "Réduire l'empreinte CO₂":
        df_alt = df_alt[df_alt['Empreinte_CO2'] < row_ref['Empreinte_CO2']].sort_values(by='Empreinte_CO2', ascending=True)
    else:
        df_alt = df_alt[df_alt['Prix_euro_kg'] < row_ref['Prix_euro_kg']].sort_values(by='Prix_euro_kg', ascending=True)

    if not df_alt.empty:
        meilleur_choix = df_alt.iloc[0]
        st.success(f"### 🎉 Alternative idéale trouvée : **{meilleur_choix['Nom']}** ({meilleur_choix['Famille']})")
        col_gain1, col_gain2 = st.columns(2)
        if objectif == "Réduire l'empreinte CO₂":
            gain_co2 = ((row_ref['Empreinte_CO2'] - meilleur_choix['Empreinte_CO2']) / row_ref['Empreinte_CO2']) * 100
            col_gain1.metric("Nouvelle Empreinte CO₂", f"{meilleur_choix['Empreinte_CO2']} kg/kg", f"-{gain_co2:.1f}% CO₂", delta_color="inverse")
            col_gain2.metric("Prix associé", f"{meilleur_choix['Prix_euro_kg']} €/kg")
        else:
            gain_prix = ((row_ref['Prix_euro_kg'] - meilleur_choix['Prix_euro_kg']) / row_ref['Prix_euro_kg']) * 100
            col_gain1.metric("Nouveau Prix", f"{meilleur_choix['Prix_euro_kg']} €/kg", f"-{gain_prix:.1f}% cher", delta_color="inverse")
            col_gain2.metric("Empreinte CO₂ associée", f"{meilleur_choix['Empreinte_CO2']} kg/kg")
            
        st.write("**Autres alternatives viables trouvées pour ces critères :**")
        st.dataframe(df_alt[colonnes_affichage], use_container_width=True)
    else:
        st.info("Aucun autre alliage ne permet d'améliorer ce critère avec ces tolérances. Essayez d'élargir les pourcentages.")

# --- ONGLET 2 : FILTRAGE STRICT & ASHBY ---
with tab2:
    st.header("📐 Cahier des Charges & Indices de Performance d'Ashby")
    
    st.markdown("### 📈 Optimisation de structure (Indices d'Ashby)")
    st.write("Sélectionnez un indice d'optimisation structurelle pour classer automatiquement les matériaux.")
    
    type_indice = st.selectbox(
        "Choisissez l'indice de performance d'Ashby à maximiser :",
        ["Aucun - Tri standard", "Composant en Traction pure (Maximiser Re / ρ)", "Composant en Flexion pure (Maximiser √Re / ρ)"]
    )
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### ⚙️ Mécanique")
        limite_elastique_min = st.slider("Limite Élastique Min (MPa)", int(df_initial['Limite_Elastique_MPa'].min()), int(df_initial['Limite_Elastique_MPa'].max()), int(df_initial['Limite_Elastique_MPa'].min()))
        module_young_min = st.slider("Module de Young Min (GPa)", int(df_initial['Module_Young_GPa'].min()), int(df_initial['Module_Young_GPa'].max()), int(df_initial['Module_Young_GPa'].min()))
    with c2:
        st.markdown("### 🌡️ Thermique")
        temp_fusion_min = st.slider("Température de Fusion Min (°C)", int(df_initial['Temp_Fusion_C'].min()), int(df_initial['Temp_Fusion_C'].max()), int(df_initial['Temp_Fusion_C'].min()))
        conductivite_min = st.slider("Conductivité Thermique Min (W/m·K)", int(df_initial['Conductivite_Thermique_W_mK'].min()), int(df_initial['Conductivite_Thermique_W_mK'].max()), int(df_initial['Conductivite_Thermique_W_mK'].min()))
    with c3:
        st.markdown("### 🌱 Éco & Coûts")
        empreinte_co2_max = st.slider("Empreinte CO₂ Max (kg/kg)", float(df_initial['Empreinte_CO2'].min()), float(df_initial['Empreinte_CO2'].max()), float(df_initial['Empreinte_CO2'].max()))
        recyclabilite_min = st.slider("Taux de Recyclabilité Min (%)", int(df_initial['Recyclabilite_pct'].min()), int(df_initial['Recyclabilite_pct'].max()), int(df_initial['Recyclabilite_pct'].min()))
        prix_max = st.slider("Prix Max (€/kg)", float(df_initial['Prix_euro_kg'].min()), float(df_initial['Prix_euro_kg'].max()), float(df_initial['Prix_euro_kg'].max()))
        
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Temp_Fusion_C'] >= temp_fusion_min) &
        (df_initial['Conductivite_Thermique_W_mK'] >= conductivite_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Recyclabilite_pct'] >= recyclabilite_min) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ].copy()
    
    # Application du tri d'Ashby
    if type_indice == "Composant en Traction pure (Maximiser Re / ρ)":
        df_filtre = df_filtre.sort_values(by='Indice_Traction', ascending=False)
    elif type_indice == "Composant en Flexion pure (Maximiser √Re / ρ)":
        df_filtre = df_filtre.sort_values(by='Indice_Flexion', ascending=False)

    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s) trouvé(s) sur 500")
    
    if not df_filtre.empty:
        st.dataframe(df_filtre[colonnes_affichage], use_container_width=True)
        
        # Bouton d'exportation CSV de la sélection
        csv_data = df_filtre[colonnes_affichage].to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="📥 Télécharger les résultats de la sélection (CSV)",
            data=csv_data,
            file_name="selection_eco_conception.csv",
            mime="text/csv"
        )
        
        st.write("### 📈 Graphique de compromis : Résistance Mécanique vs Empreinte CO₂")
        st.scatter_chart(df_filtre, x='Empreinte_CO2', y='Limite_Elastique_MPa', color='Famille')
    else:
        st.warning("Aucun alliage ne correspond. Essayez d'assouplir certains curseurs.")