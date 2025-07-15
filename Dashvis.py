# dashview_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import tempfile, os, uuid

# -------------------------------------------------
# CONFIGURATION DE LA PAGE
# -------------------------------------------------
st.set_page_config(page_title="DashView", layout="wide")
st.title("📊 DashView – Créez des dashboards en un clic")

st.markdown("""
Importez un fichier **CSV** pour générer automatiquement un tableau de bord interactif.
""")

# -------------------------------------------------
# IMPORT DU FICHIER
# -------------------------------------------------
uploaded_file = st.file_uploader("📁 Téléchargez un fichier CSV", type=["csv"])
if uploaded_file:
    try:
        # Lecture avec gestion automatique du séparateur
        df = pd.read_csv(uploaded_file, sep=",")
        if df.shape[1] == 1:
            df = pd.read_csv(uploaded_file, sep=";")

        st.success("✅ Fichier chargé avec succès !")

        # Aperçu
        with st.expander("👁️ Aperçu des données"):
            st.dataframe(df)

        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(exclude='number').columns.tolist()

        st.subheader("📈 Graphiques automatiques")
        figs = []  # Liste des figures à exporter

        # Histogramme pour les colonnes numériques
        if numeric_cols:
            num_col = st.selectbox("Choisissez une colonne **numérique** :", numeric_cols)
            fig_num = px.histogram(df, x=num_col, nbins=20,
                                   title=f"Distribution de {num_col}")
            st.plotly_chart(fig_num, use_container_width=True)
            figs.append(fig_num)

        # Diagramme en barres pour les colonnes catégorielles
        if categorical_cols:
            cat_col = st.selectbox("Choisissez une colonne **catégorielle** :", categorical_cols)
            data_cat = df[cat_col].value_counts().reset_index()
            data_cat.columns = [cat_col, "count"]  # renommer pour éviter 'index'
            fig_cat = px.bar(data_cat, x=cat_col, y="count",
                             labels={cat_col: cat_col, "count": "Nombre"},
                             title=f"Répartition des valeurs de {cat_col}")
            st.plotly_chart(fig_cat, use_container_width=True)
            figs.append(fig_cat)

        # -------------------------------------------------
        # EXPORT AU FORMAT PDF
        # -------------------------------------------------
        if figs:
            if st.button("📄 Exporter le dashboard en PDF"):
                with st.spinner("Génération du PDF…"):
                    tmpdir = tempfile.mkdtemp()
                    img_paths = []

                    # Sauvegarde de chaque figure en PNG (nécessite kaleido)
                    for i, f in enumerate(figs, 1):
                        path = os.path.join(tmpdir, f"fig{i}.png")
                        f.write_image(path)
                        img_paths.append(path)

                    # Création du PDF
                    pdf = FPDF(orientation='P', unit='mm', format='A4')
                    for img in img_paths:
                        pdf.add_page()
                        pdf.image(img, x=10, y=25, w=190)
                    pdf_path = os.path.join(tmpdir, f"dashview_{uuid.uuid4().hex}.pdf")
                    pdf.output(pdf_path)

                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="💾 Télécharger votre PDF",
                            data=file,
                            file_name="dashboard.pdf",
                            mime="application/pdf"
                        )
                st.success("PDF généré avec succès !")

    except Exception as e:
        st.error(f"Erreur lors du chargement ou du traitement du fichier : {e}")
else:
    st.info("Veuillez importer un fichier CSV pour commencer.")

st.markdown("---")
st.caption("© 2025 – NovaSolution | Powered by Streamlit")
