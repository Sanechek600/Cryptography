#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import itertools
import random
import sys

def get_alphabet(name):
    """Возвращает строку алфавита по имени."""
    if name == 'en':
        return 'abcdefghijklmnopqrstuvwxyz'
    elif name == 'ru':
        # Русский алфавит с буквой ё (33 буквы)
        return 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    else:
        return name  # пользовательская строка

def all_ngrams(alphabet, n):
    """Генерирует все возможные n-граммы в лексикографическом порядке."""
    return [''.join(p) for p in itertools.product(alphabet, repeat=n)]

def generate_key(args):
    """Создаёт файл ключа со случайной перестановкой n-грамм."""
    alphabet = get_alphabet(args.alphabet)
    n = args.n
    if n <= 0:
        print("n должно быть положительным", file=sys.stderr)
        sys.exit(1)

    ngrams = all_ngrams(alphabet, n)
    total = len(ngrams)

    if total > 200000:
        print(f"Внимание: будет сгенерировано {total} n-грамм. "
              "Это может занять много времени и места.", file=sys.stderr)

    shuffled = ngrams[:]
    random.shuffle(shuffled)

    with open(args.key, 'w', encoding='utf-8') as f:
        f.write(alphabet + '\n')
        for dst in shuffled:
            f.write(dst + '\n')

    print(f"Ключ сохранён в {args.key} ({total} n-грамм)")

def load_key(key_path):
    """Загружает ключ и строит прямое/обратное отображение."""
    with open(key_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n\r') for line in f if line.strip() != '']

    if len(lines) < 2:
        raise ValueError("Некорректный файл ключа")

    alphabet = lines[0]
    n = len(lines[1])
    srcs = all_ngrams(alphabet, n)

    if len(lines) - 1 != len(srcs):
        raise ValueError(
            f"В ключе должно быть {len(srcs)} n-грамм, "
            f"а найдено {len(lines)-1}"
        )

    enc = {src: dst for src, dst in zip(srcs, lines[1:])}
    dec = {dst: src for src, dst in enc.items()}
    return alphabet, n, enc, dec

def process_buffer(buf, n, mapping):
    """Обрабатывает непрерывную последовательность букв (без пробелов)."""
    out = []
    i = 0
    while i + n <= len(buf):
        gram = buf[i:i+n]
        out.append(mapping.get(gram, gram))
        i += n
    if i < len(buf):
        out.append(buf[i:])  # неполная n-грамма остаётся как есть
    return ''.join(out)

def process_text(text, n, mapping, alphabet_set):
    """Шифрует/дешифрует текст, сохраняя пробелы и переводы строк."""
    result = []
    buf = []
    for ch in text:
        if ch in alphabet_set:
            buf.append(ch)
        else:
            if buf:
                result.append(process_buffer(''.join(buf), n, mapping))
                buf = []
            result.append(ch)
    if buf:
        result.append(process_buffer(''.join(buf), n, mapping))
    return ''.join(result)

def encrypt(args):
    alphabet, n, enc, _ = load_key(args.key)
    alphabet_set = set(alphabet)

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    cipher = process_text(text, n, enc, alphabet_set)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(cipher)

    print(f"Зашифровано в {args.output}")

def decrypt(args):
    alphabet, n, _, dec = load_key(args.key)
    alphabet_set = set(alphabet)

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    plain = process_text(text, n, dec, alphabet_set)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(plain)

    print(f"Расшифровано в {args.output}")

def main():
    parser = argparse.ArgumentParser(description='n-граммная подстановка')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Генерация ключа
    p_gen = subparsers.add_parser('genkey', help='Сгенерировать ключ')
    p_gen.add_argument('--n', type=int, required=True, help='Размер n-граммы')
    p_gen.add_argument('--alphabet', default='en',
                       help='Алфавит: en, ru или строка символов')
    p_gen.add_argument('--key', required=True, help='Путь к файлу ключа')
    p_gen.set_defaults(func=generate_key)

    # Шифрование
    p_enc = subparsers.add_parser('encrypt', help='Зашифровать файл')
    p_enc.add_argument('--key', required=True, help='Путь к файлу ключа')
    p_enc.add_argument('--input', required=True, help='Входной текстовый файл')
    p_enc.add_argument('--output', required=True, help='Выходной текстовый файл')
    p_enc.set_defaults(func=encrypt)

    # Дешифрование
    p_dec = subparsers.add_parser('decrypt', help='Расшифровать файл')
    p_dec.add_argument('--key', required=True, help='Путь к файлу ключа')
    p_dec.add_argument('--input', required=True, help='Входной текстовый файл')
    p_dec.add_argument('--output', required=True, help='Выходной текстовый файл')
    p_dec.set_defaults(func=decrypt)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()