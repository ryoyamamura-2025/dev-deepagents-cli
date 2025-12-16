import sys
import numpy as np

def calculate_with_numpy(a, b):
    """
    NumPyを使用してaとbの四則演算を実行する関数。
    """
    # スカラー値をNumPyの配列（スカラー配列）として扱う
    # NumPyではスカラー値に対しても、標準の演算子が要素ごとの演算として機能します。
    
    try:
        # 足し算
        addition = np.add(a, b)
        # 引き算
        subtraction = np.subtract(a, b)
        # 掛け算
        multiplication = np.multiply(a, b)
        # 割り算 (通常の浮動小数点除算)
        division = np.divide(a, b)
        
        # 結果の出力
        print("-" * 30)
        print(f"入力値: a = {a}, b = {b}")
        print("-" * 30)
        print(f"足し算 (a + b)      : {addition}")
        print(f"引き算 (a - b)      : {subtraction}")
        print(f"掛け算 (a * b)      : {multiplication}")
        print(f"割り算 (a / b)      : {division}")
        print("-" * 30)
        
    except ZeroDivisionError:
        print("エラー: 0による割り算は実行できません。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    # コマンドライン引数が3つ（スクリプト名 + a + b）あるか確認
    if len(sys.argv) != 3:
        print("使用法: python calculate.py <a> <b>")
        print("例: python calculate.py 10 5")
        sys.exit(1)
        
    # コマンドライン引数を文字列として取得
    arg_a = sys.argv[1]
    arg_b = sys.argv[2]
    
    try:
        # 文字列を浮動小数点数に変換
        # NumPyで計算するために、float型に変換することが一般的です。
        a = float(arg_a)
        b = float(arg_b)
        
        calculate_with_numpy(a, b)
        
    except ValueError:
        print("エラー: 入力された引数が有効な数値ではありません。")
        print(f"受け取った引数: a='{arg_a}', b='{arg_b}'")
        sys.exit(1)