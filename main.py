import re
from typing import List
from rich.table import Table
from rich.console import Console

keywords = {
    'UNION', 'INTERSECT', 'TIMES', 'JOIN',
    'WHERE', 'DIVIDE BY', 'RENAME',
    'Semijoin', 'Semiminus', 'SUMMARIZE',
    'INNER', 'LEFT', 'RIGHT', 'CREATE',
    'TABLE', 'DROP', 'ALTER', 'ADD',
    'INSERT', 'VALUES', 'INTO', 'UPDATE',
    'DELETE', 'BeginRA', 'EndRA'
}
types = {
    "INTEGER", 'TEXT'
}
keywords.update(types)
keywords.update(set(map(lambda language_type: language_type.lower(), types)))

operators_with_information = {
    'assignment': {'walrus': ':=',
                   'assignment': '='},
    'comparison': {'equals': '==',
                   'not equals': '!=',
                   'greater or equals': '>=',
                   'less or equals': '<=',
                   'greater than': '>',
                   'less than': '<'},
    'mathematical': {'plus': r'\+',
                     'minus': '-',
                     'multiply': r'\*',
                     'divide': '/'}
}
brackets = {
    'square opening': r'\[',
    'square closing': r'\]',
    'round opening': r'\(',
    'round closing': r'\)',
    'curly opening': r'\{',
    'curly closing': r'\}',
}
symbols = {
    'coma': ',',
    'point': r'\.',
    'semicolon': ';',
}
operators = {}
for operators_type, operators_with_name in operators_with_information.items():
    operators_list = [
        operator for operator_name, operator in operators_with_name.items()
    ]
    operators[operators_type] = '(' + '|'.join(operators_list) + ')'

rules = {
    'keyword': '(' + '|'.join(keywords) + ')',
    'id3': r'[a-zA-Z]+_[a-zA-Z]+\d*',
    'id2': r'[a-zA-Z]+_\w*',
    'number': r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?',
    'simple_quoters': "'.*'",
    'double_quoters': '".*"',

}
rules = {**rules, **operators}
rules = {**rules, 'bracket': '[' + ''.join(brackets.values()) + ']'}
rules = {**rules, 'symbol': '[' + ''.join(symbols.values()) + ']'}


class Token:
    def __init__(self, token_type: str, name: str, value, start: int, length: int, position: int) -> None:
        super().__init__()
        self.type = token_type
        self.name = name
        self.value = value
        self.start = start
        self.length = length
        self.position = position

    def __str__(self) -> str:
        return "token_type:\t" + self.type \
               + "\tname:\t" + self.name \
               + "\tvalue:\t" + str(self.value) \
               + "\tstart:\t" + str(self.start) \
               + "\tlength:\t" + str(self.length) \
               + "\tposition:\t" + str(self.position)


def get_token_name(token_type: str, token_value: str) -> str:
    global operators_with_information
    global brackets
    global symbols
    global rules

    if token_type == 'bracket':
        for bracket_name, bracket_value in brackets.items():
            if re.match(bracket_value, token_value):
                return bracket_name
    elif token_type == 'operator':
        for operator_type, operator_info in operators_with_information.items():
            for operator_name, operator_value in operator_info.items():
                if re.match(operator_value, token_value):
                    return operator_name
    elif token_type == 'undefined':
        return 'undefined'
    elif token_value == 'symbol':
        for symbol_name, symbol_value in symbols.items():
            if re.match(symbol_value, token_value):
                return symbol_name
    else:
        for rule_name, regex in rules.items():
            if token_type == rule_name:
                return token_type


def get_matches(string: str) -> List[list]:
    global rules
    matches = []
    while string:
        leftmost_token = None
        token_rule_name = ''
        for rule_name, rule in rules.items():
            regex_result = re.search(rule, string)
            if regex_result:
                if leftmost_token:
                    if regex_result.span()[0] < leftmost_token.span()[0]:
                        leftmost_token = regex_result
                        token_rule_name = rule_name
                else:
                    leftmost_token = regex_result
                    token_rule_name = rule_name
        if leftmost_token:
            matches.append([token_rule_name, leftmost_token.group()])

            if left_tail := string[:leftmost_token.span()[0]].split():
                for undefined_token in left_tail:
                    matches.append(['undefined', undefined_token])
            string = string[leftmost_token.span()[1]:]
        else:
            if right_tail := string.split():
                for undefined_token in right_tail:
                    matches.append(['undefined', undefined_token])
            string = ''
    return matches


def convert_matches_to_tokens(matches):
    tokens = []
    token_position = 1
    start = 1
    for match in matches:
        token_type = match[0]
        token_value = match[1]
        if token_type in ['id', 'keyword']:
            token_name = token_value
        else:
            token_name = get_token_name(token_type, match[1])
        for added_token in tokens:
            if token_value == added_token.value:
                tokens.append(Token(token_type, token_name, token_value, start, len(match[1]), added_token.position))
                start += len(token_value)
                break
        else:
            tokens.append(Token(token_type, token_name, token_value, start, len(match[1]), token_position))
            start += len(token_value)
            token_position += 1
    return tokens


def analyze_and_output(str_to_analyse):
    matches = get_matches(str_to_analyse)

    console = Console()
    table = Table(show_header=True, header_style='bold magenta')

    table.add_column("Token")
    table.add_column("Lexeme")
    table.add_column("Start")
    table.add_column("Length")
    table.add_column("Position")

    for token in convert_matches_to_tokens(matches):
        table.add_row(token.type, token.value, str(token.start), str(token.length), str(token.position))
    console.print(table)


def main():
    example1 = "T__12 := TE__4 INTERSECT (EM__L UNION DEP__2 WHERE salary_s1 > 4015)"
    example2 = "BeginRA " \
               "CREATE TABLE fds sd group__12 (num_g12 integer, name_g12 text (60));" \
               "INSERT INTO group__12 VALUES (1, 'Цикл ГСЕ дисциплін вибору')" \
               "EndRA  dawd asdw"
    analyze_and_output(example1)
    analyze_and_output(example2)


if __name__ == '__main__':
    main()
