from flask import Flask, request, jsonify

import pandas as pd
import io
import base64

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)


# =========================
# 共用函式：產生 Heatmap
# =========================
def create_map(df_map, title, vmin, vmax):

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        df_map,
        cmap="rainbow",
        vmin=vmin,
        vmax=vmax
    )

    plt.title(title)

    buffer = io.BytesIO()

    plt.savefig(
        buffer,
        format="png",
        bbox_inches="tight"
    )

    plt.close()

    buffer.seek(0)

    image_base64 = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

    return image_base64


# =========================
# 首頁測試
# =========================
@app.route("/", methods=["GET"])
def home():

    return "Yield Map API is running"


# =========================
# Yield分析
# =========================
@app.route("/yield", methods=["POST"])
def yield_map():

    data = request.get_json()

    csv_base64 = data.get("csv_base64")
    file_name = data.get("file_name", "upload.csv")

    if not csv_base64:

        return jsonify({
            "error": "missing csv_base64"
        }), 400

    # =====================
    # 讀CSV
    # =====================

    csv_bytes = base64.b64decode(csv_base64)

    df = pd.read_csv(
        io.BytesIO(csv_bytes),
        skiprows=7
    )

    # =====================
    # Yield計算
    # =====================

    total_qty = len(df)

    good_df = df[
        (df["Ir1"] >= 0) &
        (df["Ir1"] <= 0.2) &
        (df["Vf1"] >= 2.2) &
        (df["Vf1"] <= 3.5) &
        (df["Vf2"] >= 2.9) &
        (df["Vf2"] <= 3.3)
    ]

    good_qty = len(good_df)

    yield_value = round(
        good_qty / total_qty * 100,
        2
    )

    # =====================
    # POD MAP
    # =====================

    pod_map = pd.pivot_table(
        df,
        values="Iv2",
        columns="X",
        index="Y",
        aggfunc="mean"
    )

    pod_map = (
        pod_map
        .sort_index(ascending=False)
        .sort_index(axis=1, ascending=True)
    )

    pod_map_base64 = create_map(
        pod_map,
        "POD MAP",
        400,
        1000
    )

    # =====================
    # VF2 MAP
    # =====================

    vf2_map = pd.pivot_table(
        df,
        values="Vf2",
        columns="X",
        index="Y",
        aggfunc="mean"
    )

    vf2_map = (
        vf2_map
        .sort_index(ascending=False)
        .sort_index(axis=1, ascending=True)
    )

    vf2_map_base64 = create_map(
        vf2_map,
        "VF2 MAP",
        2.8,
        3.3
    )

    # =====================
    # 回傳結果
    # =====================

    return jsonify({

        "file_name": file_name,

        "total_qty": total_qty,

        "good_qty": good_qty,

        "yield": yield_value,

        "pod_map_base64": pod_map_base64,

        "vf2_map_base64": vf2_map_base64

    })


# =========================
# 啟動
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080
    )
