# -- coding: utf-8 --

import PySimpleGUI as sg
import unicodedata as ud
import pyperclip
from pathlib import Path

def __default_setting(width=60, height=20, threshold=20):
    fname = Path('setting.ini')
    if not fname.exists():
        with open(fname, "w") as f:
            f.write(f'wordNumRow wordNumCol printLine {width} {height} {threshold}')
    else:
        with open(fname, 'r') as f:
            sets = f.read().split(" ")
        width, height, threshold = int(sets[3]), int(sets[4]), int(sets[5])
    return width, height, threshold

def __length_counter(word):
    isHankaku = ud.east_asian_width(word)
    # Na:半角英数，H:半角カタカナ
    if (isHankaku == 'Na') or (isHankaku == 'H'):
        return 1
    else:
        return 2

def __convert_text(input_text="t\ne\ns\nt\n", line_word_length=120, max_line=19):
    inputs = input_text.split("\n")
    row = 0
    out = ""
    for line in inputs: # 1行ごと読み込み
        row += 1    # 行数追加
        if 2*len(line) <= line_word_length:    # 全部全角だとして1行の文字数以下ならスルー
            out += line
        else:   # 1行の文字が多すぎるとき
            num_word = 0
            for i, word in enumerate(line): # 1文字ずつ読み込み
                num_word += __length_counter(word)  # 半角なら1，全角なら2を追加
                if num_word < line_word_length:
                    out += word
                else:   # 1行の文字数が許容数を超えるとき
                    num_word = __length_counter(word)  # 文字数のリセット
                    out += '\n' + word  # 改行してから追記
                    row += 1    # 行数の追加

        out += '\n'

    stat = 0
    if row > max_line:
        stat = 1
    return out, stat

def __create_layout(outputs, offset=0):
    layout = []
    for row, out in enumerate(outputs):
        number = str(1 + row + offset).zfill(3)
        layout.append([sg.Text(number), sg.Button('Copy', key=f'bt{number}'),
                       sg.InputText(default_text=out, size=(60, 1), key=f'txt{number}')])
    return layout

def __control_window(layout):
    window = sg.Window('ボタンを押すとクリップボードにコピーされます', layout)

    while True:
        event, values = window.read()

        if event is None:
            print('exit')
            break

        if 'bt' in event:
            key = f'txt' + event.replace('bt', '')
            pyperclip.copy(values[key])

    window.close()
    return 0

def __create_window(output_text):
    outputs = output_text.split('\n')   # 改行で分離
    print(outputs)

    if len(outputs) < threshold:
        out = [outputs]
    else:
        count = 0
        out, out_in = [], []
        for item in outputs:
            if count == threshold:
                out.append(out_in)
                out_in = []
                count = 0
            out_in.append(item)
            count += 1
        out.append(out_in)

    for i, out_sep in enumerate(out):
        layout = __create_layout(out_sep, offset=int(i*threshold))
        __control_window(layout)

    return 0

def main():
    #  セクション1 - オプションの設定と標準レイアウト
    sg.theme('Dark Blue 3')

    layout = [
        [sg.Multiline(default_text='ここにテキストをコピー', size=(width, height), border_width=2, key='txt1')],
        [sg.Text('行の文字数'), sg.InputText(default_text='120', size=(10, 1), key='mojisu')],
        [sg.Text('行の最大数'), sg.InputText(default_text='19', size=(10, 1), key='gyosu')],
        [sg.Submit('テキスト出力')]
    ]

    # セクション 2 - ウィンドウの生成
    window = sg.Window('レポート作成支援ツール(仮)', layout, resizable=True)

    # セクション 3 - イベントループ
    while True:
        event, values = window.read()

        if event is None:
            print('exit')
            break

        if event == 'テキスト出力':
            # ポップアップ
            out, status = __convert_text(input_text=values['txt1'], line_word_length=int(values['mojisu']), max_line=int(values['gyosu']))
            if status == 1:
                sg.popup(f'警告：行の最大数を超えています\n\t{threshold}行ずつ表示します')
            __create_window(out)

    # セクション 4 - ウィンドウの破棄と終了
    window.close()

if __name__ == '__main__':
    width, height, threshold = __default_setting()
    main()