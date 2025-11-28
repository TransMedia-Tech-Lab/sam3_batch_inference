# SAM3 Docker Setup

Docker を使用して SAM3 の推論環境を簡単に構築・実行する方法です。

## 前提条件

*   Docker Engine がインストールされていること
    *   Linuxの場合、権限エラーが出る場合は `sudo` を付けて実行するか、ユーザーを `docker` グループに追加してください。
*   NVIDIA GPU を搭載したマシンであること
*   [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) がインストールされていること
*   Hugging Face のアクセストークンを持っていること（SAM3 のモデルダウンロードに必要）

## セットアップ手順

1.  **Hugging Face トークンの設定**

    プロジェクトのルートディレクトリに `.env` ファイルを作成し、Hugging Face のトークンを記述します。
    （`.env.example` をコピーして使用できます）

    ```bash
    cp .env.example .env
    # .env ファイルを開き、トークンを書き換えてください
    # HF_TOKEN=your_actual_token_starts_with_hf_...
    ```

2.  **Docker イメージのビルド**

    ```bash
    docker compose build
    ```

3.  **コンテナの起動**

    以下のコマンドで環境を起動します。
    （初回実行時は、Dockerイメージのビルドとモデルのダウンロードが行われるため時間がかかります）

    ```bash
    docker compose up -d
    ```

4.  **推論の実行**

    コンテナが起動したら、以下のコマンドで推論を実行します。

    ```bash
    docker compose exec sam3 uv run run_inference.py
    ```

    実行が完了すると、`results` ディレクトリに `result.jpg` が生成されます。

    ※ モデルはDockerボリュームにキャッシュされるため、2回目以降の実行は高速になります。

    終了するには：
    ```bash
    docker compose down
    ```

## カスタマイズ

*   **コンテナ内での作業**:
    ```bash
    docker compose exec sam3 /bin/bash
    ```
    でコンテナ内のシェルに入り、自由にコマンドを実行できます。
