# VanningLayout

## MCP server

This repository includes a FastMCP stdio server that exposes the Step6
near-minimum-bin 3D packing solver as an AI tool.

Registered tool:

- `pack_vanning_layout`

The tool accepts JSON-like item and container data, runs
`pack_min_bin_count_3d_by_destination`, and returns JSON-serializable container
counts, bin summaries, center-of-gravity data, and item placements.

Install the MCP dependency:

```powershell
pip install -r requirements-mcp.txt
```

Run the MCP server over stdio:

```powershell
python -m vanning.mcp_server
```

For the detailed input/output format and Codex MCP configuration example, see
[docs/mcp_server.md](docs/mcp_server.md). The dependency list is
[requirements-mcp.txt](requirements-mcp.txt).

20ft コンテナ向けのバンニングレイアウト最適化コードです。  
現時点では Step1 から Step6 まで段階的に実装されており、Step6 では

- 使用コンテナ本数の削減
- 重量制約
- 行先分離
- 3D 配置
- 簡易安定条件
- 重心制約

を満たす実行可能解を探索します。

## 問題設定

問題設定の詳細は [vanning_design_problem.md](vanning_design_problem.md) を参照してください。

## 入力データフォーマット

現状の solver が直接受け取る入力は、`WeightedItem3D` の配列です。

各要素は次の情報を持ちます。

| 項目 | 型 | 内容 |
| --- | --- | --- |
| `item_id` | `str` | 箱ID |
| `length` | `float` | 箱の長さ [mm] |
| `width` | `float` | 箱の幅 [mm] |
| `height` | `float` | 箱の高さ [mm] |
| `weight_kg` | `float` | 重量 [kg] |
| `dest` | `str` | 行先 (`"X"` / `"Y"` など) |
| `allow_rotate` | `bool` | 水平回転 90° を許可するか |

実装上のエントリポイント:

- [WeightedItem3D](vanning/step3_weighted_3d.py)
- [pack_min_bin_count_3d_by_destination](vanning/step6_bin_count_minimization_3d.py)

今回の問題インスタンスの 80 箱データは [problem_spec.py](vanning/problem_spec.py) に定義されており、次の helper で読み込めます。

- [build_step3_weighted_realdata_items](vanning/problem_spec.py)

## 出力データフォーマット

現時点の出力は、提出物専用の固定帳票ではなく、solver 戻り値と実行スクリプトのテキスト出力です。

### 1. Solver の戻り値

Step6 の戻り値は `MinimizedBinCountPackingSummary3D` です。

| 項目 | 内容 |
| --- | --- |
| `bins` | 最終コンテナ一覧 |
| `initial_bin_count` | Step5 初期解のコンテナ本数 |
| `bin_count` | Step6 後のコンテナ本数 |
| `total_weight_kg` | 全コンテナの総重量 |
| `max_observed_center_offset_mm` | 最大重心ずれ |

関連定義:

- [MinimizedBinCountPackingSummary3D](vanning/step6_bin_count_minimization_3d.py)
- [CenterBalancedBin3D](vanning/step4_center_of_gravity_3d.py)
- [WeightedPlacedItem3D](vanning/step3_weighted_3d.py)

各コンテナ (`CenterBalancedBin3D`) は、配置済み箱の一覧 `placements` を持ちます。  
各配置要素 (`WeightedPlacedItem3D`) は次を持ちます。

| 項目 | 内容 |
| --- | --- |
| `item.item_id` | 箱ID |
| `item.weight_kg` | 重量 |
| `item.dest` | 行先 |
| `x, y, z` | 左下手前角の配置座標 [mm] |
| `length, width, height` | 実際に使用した寸法 [mm] |
| `rotated` | 90° 回転したかどうか |

### 2. 実行スクリプトの標準出力

`scripts/run_step6_realdata_3d.py` は次を出力します。

- 入力箱数
- Step5 初期本数
- Step6 最終本数
- 使用体積 / 総体積 / 未使用体積
- 重心ずれの総和 / 平均 / 最大
- 各コンテナごとの
  - 行先
  - 箱数
  - 重量
  - 未使用体積
  - 重心ずれ

## 最適化の実行方法

今回の realdata インスタンスに対して Step6 を実行するには、リポジトリルートで次を実行します。

```powershell
python scripts\run_step6_realdata_3d.py
```

Step6 の本体は Step5 の実行可能解を初期解として使い、その後に行先ごとに再分割探索を行って、コンテナ本数を 1 本ずつ減らせるか試します。

## 出力解の可視化方法

Step6 の 3D 可視化アーティファクトを生成するには、次を実行します。

```powershell
python scripts\generate_step6_bin_count_minimization_explanation.py
```

生成物:

- `artifacts/step6_bin_count_minimization_explanation/README.md`
- `artifacts/step6_bin_count_minimization_explanation/example/*.svg`
- `artifacts/step6_bin_count_minimization_explanation/realdata/*.svg`

この可視化では次を確認できます。

- Step5 初期解と Step6 改善後の比較
- 各コンテナの top-down / orthographic / isometric 表示
- 使用体積 / 未使用体積 / 利用率
- 各コンテナの中心からの重心ずれ
- realdata 全体のコンテナ本数と評価指標

## 補足

現時点では、`vanning_design_problem.md` の提出物形式そのものを出力する専用 exporter は未実装です。  
現在は solver 戻り値、標準出力、可視化 README / SVG によって解を確認する構成です。
