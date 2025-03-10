from parsers import AvitoParser
parser = AvitoParser("BMW", "X5")
print(parser.parse()[:5])  # Вывести первые 5 цен