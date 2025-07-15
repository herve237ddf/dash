# dashview_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import tempfile, os, uuid
import streamlit_authenticator as stauth

# ----- Authentification -----
hashed_passwords = [
    'pbkdf2:sha256:260000$2zYFzhyCZ5QM5Jzy$5c7256b26b70c9fdb0e1e428c3c0666751df8cb97fe1f4fca701526f6b8d6f0a'
]

credentials = {
    "usernames": {
        "admin": {
            "name": "Administrateur",
            "password": hashed_passwords[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name='dashview_cookie',
    key='random_signature_key',
    cookie_expiry_days=1
)

name, auth_status, username = authenticator.login('🔐 Connexion', 'main')

if auth_status is False:
    st.error("Nom d’utilisateur ou mot de passe incorrect.")
elif auth_status is None:
    st.warning("Veuillez entrer vos identifiants.")
else:
    authenticator.logout('Se déconnecter', 'sidebar')
    st.sidebar.write(f"👋 Bonjour {name}")

    st.set_page_config(page_title="DashView", layout="wide")
    st.title("📊 DashView – Créez des dashboards en un clic")

    st.markdown("Importez un fichier **CSV** et préparez vos données avant de créer des visualisations automatiques.")

    uploaded_file = st.file_uploader("📁 Téléchargez un fichier CSV", type=["csv"])
    if uploaded_file:
        try:
            # 🔍 ÉTAPE 1 – Préparation des données
            st.header("🧹 Étape 1 : Nettoyage rapide des données")

            header_row = st.number_input("📍 Ligne contenant les en-têtes (0-indexé)", min_value=0, max_value=10, value=0)
            df_raw = pd.read_csv(uploaded_file, header=header_row)

            st.subheader("👁️ Aperçu brut")
            st.dataframe(df_raw.head())

            # Supprimer colonnes inutiles
            cols_to_drop = st.multiselect("❌ Colonnes à supprimer", df_raw.columns.tolist())
            df_clean = df_raw.drop(columns=cols_to_drop)

            # Gestion des valeurs manquantes
            missing_action = st.selectbox("🕳️ Que faire des valeurs manquantes ?", ["Ne rien faire", "Supprimer les lignes", "Remplacer par 0", "Remplacer par la moyenne"])
            if missing_action == "Supprimer les lignes":
                df_clean.dropna(inplace=True)
            elif missing_action == "Remplacer par 0":
                df_clean.fillna(0, inplace=True)
            elif missing_action == "Remplacer par la moyenne":
                df_clean.fillna(df_clean.mean(numeric_only=True), inplace=True)

            # Aperçu final
            st.success("✅ Données nettoyées !")
            st.dataframe(df_clean)

            # 🔎 Colonnes
            numeric_cols = df_clean.select_dtypes(include='number').columns.tolist()
            categorical_cols = df_clean.select_dtypes(exclude='number').columns.tolist()

            st.header("📊 Étape 2 : Visualisations automatiques")
            figs = []

            if numeric_cols:
                num_col = st.selectbox("📈 Colonne numérique :", numeric_cols)
                fig_num = px.histogram(df_clean, x=num_col, nbins=20, title=f"Distribution de {num_col}")
                st.plotly_chart(fig_num, use_container_width=True)
                figs.append(fig_num)

            if categorical_cols:
                cat_col = st.selectbox("📊 Colonne catégorielle :", categorical_cols)
                data_cat = df_clean[cat_col].value_counts().reset_index()
                fig_cat = px.bar(data_cat, x='index', y=cat_col,
                                 labels={'index': cat_col, cat_col: "Nombre"},
                                 title=f"Répartition des valeurs de {cat_col}")
                st.plotly_chart(fig_cat, use_container_width=True)
                figs.append(fig_cat)

            # 📄 Export PDF
            if figs:
                if st.button("📄 Exporter le dashboard en PDF"):
                    with st.spinner("Génération du PDF…"):
                        tmpdir = tempfile.mkdtemp()
                        img_paths = []

                        for i, f in enumerate(figs, 1):
                            path = os.path.join(tmpdir, f"fig{i}.png")
                            f.write_image(path)
                            img_paths.append(path)

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
                        st.success("PDF généré !")

        except Exception as e:
            st.error(f"Erreur lors du traitement : {e}")
    else:
        st.info("Veuillez importer un fichier CSV pour commencer.")

    st.markdown("---")
    st.caption("© 2025 – NovaSolution | Powered by Streamlit")
