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
cp <推論したい画像のパス>/*.jpg image/
# または
cp <推論したい画像のパス>/*.png image/
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

# マスクを個別保存する場合（デバッグや後処理に便利）
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "soccer players" \
  --save-individual-masks

# サンプル画像で動作確認する場合
docker compose exec sam3 \
  uv run run_inference.py \
  --prompt "truck" \
  --run-sample
```

結果は `results/` ディレクトリに保存されます。

---

## 詳細説明

### SAM3 について

SAM3 (Segment Anything Model v3) は、画像とテキストを同時に理解して任意の対象をセグメントする大規模ビジョンモデルです。テキストプロンプトで「どのような対象をセグメントしたいか」を指定すると、対応する領域のマスクを返します。

**主な特徴:**
- テキストベースのセグメンテーション（従来の座標指定が不要）
- 複数オブジェクトの同時検出
- 高精度なマスク生成

本リポジトリでは、公式チェックポイントをコンテナ内で自動取得し、フォルダ内の複数画像に対するバッチ処理を簡単に実行できます。

### セットアップの詳細

1. https://transmediatechlab.esa.io/posts/291 にアクセスし、研究室用の Hugging Face Token を取得します。
2. `.env` に `HF_TOKEN=<your_token>` を設定します。
3. `image` フォルダには推論したい画像ファイル（jpg/png など）を配置します。

### Docker環境について

`docker-compose.yml` では以下のディレクトリをマウントしています：
- `./image:/app/sam3/image` - 入力画像フォルダ
- `./results:/app/sam3/results` - 出力結果フォルダ

ホスト側で準備したファイルがコンテナ内でそのまま利用でき、結果もホスト側に保存されます。


### `run_inference.py` のオプション

スクリプトは以下のようなオプションを持ちます。

| オプション | 説明 | 既定値 |
| --- | --- | --- |
| `--image-dir` | 入力画像ディレクトリのパス | `./image` |
| `--prompt` | セグメンテーション対象を指定するテキスト | 対話入力 |
| `--prompt-file` | プロンプトを記載したテキストファイルのパス | なし |
| `--results-dir` | 結果を保存するディレクトリのパス | `./results` |
| `--save-individual-masks` | 各マスクを個別のPNGファイルとして保存 | 無効 |
| `--run-sample` | サンプル画像でも推論を実行（動作確認用） | 無効 |
| `--sample-url` | `--run-sample` で使用する画像のURL | SAM3 公式デモ画像 |

### オプションを使った実行例

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

**必ず生成されるファイル:**
- `results/<元ファイル名>_result.jpg`
  - 元画像に検出されたマスクを色付きで重ねた可視化画像
  - 複数のマスクが検出された場合は異なる色で表示されます
  - 例: `image001.jpg` → `results/image001_result.jpg`

**`--save-individual-masks` 使用時に追加生成:**
- `results/<元ファイル名>_mask_00.png`, `_mask_01.png`, ...
  - 各マスクを個別の二値画像として保存（白=対象、黒=背景）
  - マスクの詳細確認や、別のツールでの後処理に使用可能
  - 例: `image001.jpg` から2つのマスクが検出 → `image001_mask_00.png`, `image001_mask_01.png`

**カスタマイズ:**
マスクの色や透明度を変更したい場合は、`run_inference.py` 内の `MASK_COLORS` 定数や `visualize_masks` 関数の `alpha` 値を調整してください。

### プロンプトの指定方法

**3つの指定方法:**
1. **コマンドラインで直接指定:** `--prompt "検出したい対象"`
2. **ファイルから読み込み:** `--prompt-file prompt.txt`（ファイル全体がプロンプトとして使用されます）
3. **対話的に入力:** オプションを指定しない場合、実行時に入力が求められます

**効果的なプロンプトのコツ:**
- シンプルで具体的な英語表現が推奨（例: `"person"`, `"car"`, `"ball"`）
- 日本語ではうまく動作しません

## トラブルシューティング

- **`results/...` に保存できない**: ホスト側 `results` ディレクトリが無いか、ボリュームマウントがずれている可能性があります。`mkdir -p results` の後にコンテナを再作成してください。
- **マスクが 1 枚しか表示されない**: SAM3 が返す `masks` の数が 1 の可能性があります。`--save-individual-masks` で出力された二値マスクを確認し、別のプロンプト（短い英語など）も試してください。
- **チェックポイントが取得できない**: Hugging Face のログインやリポジトリアクセス権の確認が必要です。必要に応じて `huggingface-cli login` をやり直してください。

