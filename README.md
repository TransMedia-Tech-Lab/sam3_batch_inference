# SAM3 Batch Inference Helper

Meta の SAM3 を使って画像フォルダ全体に対してテキストプロンプトによるセグメンテーションを行うための簡易スクリプトと Docker 環境です。

## クイックスタート

### 1. 事前準備

まず、必要なディレクトリを作成し、Hugging Face Token を設定します：

```bash
# 必要なディレクトリを作成
mkdir -p results image

# 環境設定ファイルを作成
cp .env.example .env
```

次に、`.env` ファイルを編集して Hugging Face Token を設定してください：

1. https://transmediatechlab.esa.io/posts/291 にアクセスして研究室用の Hugging Face Token を取得
2. `.env` ファイルを開いて `HF_TOKEN=<取得したトークン>` を設定

最後に、推論したい画像を配置します：

```bash
# 推論したい画像を image フォルダに配置
cp /path/to/your/images/*.jpg image/
# または
cp /path/to/your/images/*.png image/
```

### 2. コンテナ起動

```bash
docker compose up -d --build
```

### 3. 推論実行

```bash
# 基本的な実行例
docker compose exec sam3 \
  uv run run_inference.py

# 対話型を使用しないで、プロンプトを指定する場合
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "soccer players"

# マスクを個別保存する場合
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "soccer players" \
  --save-individual-masks

# サンプル画像でも試す場合
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "soccer players" \
  --save-individual-masks \
  --run-sample
```

結果は `results/` ディレクトリに保存されます。

---

## 詳細説明

### SAM3 について

SAM3 (Segment Anything Model v3) は、画像とテキストを同時に理解して任意の対象をセグメントする大規模ビジョンモデルです。画像をセットしてテキストで「どのような対象をセグメントしたいか」を伝えると、対応するマスクを返します。本リポジトリでは公式チェックポイントをコンテナ内で取得し、バッチ処理を自動化しています。

### セットアップの詳細

1. https://transmediatechlab.esa.io/posts/291 にアクセスし、研究室用の Hugging Face Token を取得します。
2. `.env` に `HF_TOKEN=<your_token>` を設定します。
3. `image` フォルダには推論したい画像ファイル（jpg/png など）を配置します。
4. `docker-compose.yml` では `./image:/app/sam3/image` と `./results:/app/sam3/results` をマウントしているため、ホスト側で準備したフォルダがコンテナから利用されます。

### `run_inference.py` のオプション

スクリプトは以下のようなオプションを持ちます。

| オプション | 説明 | 既定値 |
| --- | --- | --- |
| `--image-dir` | 入力画像ディレクトリ | `./image` |
| `--prompt` | セグメンテーション用テキストプロンプト | 対話入力 |
| `--prompt-file` | プロンプトを記載したテキストファイル | なし |
| `--results-dir` | 可視化画像・マスクを保存するディレクトリ | `results` |
| `--save-individual-masks` | すべてのマスクを個別 PNG として保存 | 無効 |
| `--run-sample` | 既定のサンプル画像（トラック画像）でも推論を実行 | 無効 |
| `--sample-url` | `--run-sample` で利用する画像 URL | SAM3 デモ画像 |

### 詳細な実行例

```bash
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "soccer players" \
  --save-individual-masks \
  --run-sample
```

- 指定フォルダ内の各画像に対して、SAM3 モデルを 1 度ロードしたまま順に推論します。
- `results/<ファイル名>_result.jpg` にカラーオーバーレイ付きの可視化画像が保存されます。
- `--save-individual-masks` を付与すると、`results/<ファイル名>_mask_XX.png` として二値マスクも出力され、マスクが見えていないように感じる場合のデバッグに使えます。
- `--run-sample` を指定すると、フォルダ処理後に `--sample-url` の画像（既定は Segment Anything のデモ画像）をダウンロードして同一プロンプトで処理します。

### 出力内容

- `results/<ファイル名>_result.jpg`: 元画像に検出済みマスクを半透明で重ねた可視化。複数マスクは色違いで塗り分けられます。
- `results/<ファイル名>_mask_XX.png`: `--save-individual-masks` 有効時に生成される白黒マスク。白が推論対象、黒が背景です。デバッグや後段処理に利用できます。

可視化結果はマスクの信頼度やオーバーラップがわかるよう半透明化しています。必要に応じて `MASK_COLORS` やアルファ値 (`visualize_masks` 内の `alpha`) を調整してください。

### プロンプトの指定方法

- `--prompt` で直接文字列を渡す。
- `--prompt-file prompt.txt` のようにファイルを指定するとファイル全体がプロンプトとして使われます。
- どちらも指定しない場合は、実行時に対話的に入力を求められます。

## トラブルシューティング

- **`results/...` に保存できない**: ホスト側 `results` ディレクトリが無いか、ボリュームマウントがずれている可能性があります。`mkdir -p results` の後にコンテナを再作成してください。
- **マスクが 1 枚しか表示されない**: SAM3 が返す `masks` の数が 1 の可能性があります。`--save-individual-masks` で出力された二値マスクを確認し、別のプロンプト（短い英語など）も試してください。
- **チェックポイントが取得できない**: Hugging Face のログインやリポジトリアクセス権の確認が必要です。必要に応じて `huggingface-cli login` をやり直してください。

