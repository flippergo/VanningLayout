# Step3 重量制約つき 3D 配置の見方

Step3 では、Step2 の 3D 配置に対して、重量上限と積み上げ安定性の確認を追加します。

実装しているルールは次のとおりです。

1. 行先ごとに箱を分け、重い順に重量 bin へ割り当てる
2. 各重量 bin に対して Step2 の 3D 配置を行う
3. 各 bin の総重量が `max_weight_kg` を超えないことを確認する
4. 配置後に、各箱の重心の鉛直投影が床または支持面に入ることを確認する

## 例題

「空間的には 1 bin に入るが、重量上限のため 2 bin に分かれる」例を使います。

- コンテナ: `L=6000, W=3000, H=3000`
- 重量上限: `12kg`
- 箱A1: `1000x1000x1000, 7kg`
- 箱A2: `1000x1000x1000, 7kg`
- 箱A3: `1000x1000x1000, 5kg`

この例では `7 + 7 + 5 = 19kg` なので、Step3 は 2 bin に分けます。

### bin 1

![Step3 weighted example bin1](step3_weighted_3d_example_bin01.svg)

![Step3 weighted isometric bin1](step3_weighted_3d_example_isometric_bin01.svg)

### bin 2

![Step3 weighted example bin2](step3_weighted_3d_example_bin02.svg)

![Step3 weighted isometric bin2](step3_weighted_3d_example_isometric_bin02.svg)

## 説明レポートの生成

説明用レポートと本番データの SVG は次で再生成できます。

```powershell
python scripts\generate_step3_weighted_3d_explanation.py
```

出力先:

- `artifacts/step3_weighted_3d_explanation/README.md`
- `artifacts/step3_weighted_3d_explanation/example/*.svg`
- `artifacts/step3_weighted_3d_explanation/realdata/*.svg`

## 読み方

- 3 面図では、箱の位置と積み上げ方を確認します
- 立体図では、前後関係と高さ方向の重なりを確認します
- タイトルの `kg` 表示で、その bin の重量使用量を確認します
