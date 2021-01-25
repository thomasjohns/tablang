from typing import List
from typing import NoReturn
from typing import Optional

from tablang.ast import Module
from tablang.ast import Definition
from tablang.ast import Transform
from tablang.ast import Test
from tablang.ast import RuleBlock
from tablang.ast import AliasBlock
from tablang.ast import HeaderBlock
from tablang.ast import ValueBlock
from tablang.ast import HeaderRule
from tablang.ast import Pipeline
from tablang.ast import Operation
from tablang.ast import RValue
from tablang.ast import Header
from tablang.ast import String
from tablang.ast import Name
from tablang.token import Token
from tablang.token import TokenKind


TRANSFORM = 'transform'
TEST = 'test'
ALIASES = 'aliases'
HEADERS = 'headers'
VALUES = 'values'
KEYWORDS = {
    TRANSFORM,
    TEST,
    ALIASES,
    HEADERS,
    VALUES,
}

# TODO: perhaps there is be a better way to manage build-in functions
TRIM = 'trim'
TITLE = 'title'
REPLACE = 'replace'
ADD = 'add'
MULT = 'mult'
SQUARE = 'square'
BUILT_IN_FUNCTIONS = {
    TRIM,
    TITLE,
    REPLACE,
    ADD,
    MULT,
    SQUARE,
}

RESERVED_NAMES = KEYWORDS | BUILT_IN_FUNCTIONS


class Parser:
    def __init__(self, tokens: List[Token], filename: str) -> None:
        self.tokens = tokens
        self.filename = filename

        self.token_index = -1
        self.cur_token = Token(TokenKind.INVALID, None, (0, 0))

    def error(self, message: str) -> NoReturn:
        print('Syntax Error:')
        print(message)
        print(f'In file {self.filename}.')
        exit(1)

    def error_expecting(self, *kinds: TokenKind) -> None:
        if len(kinds) == 1:
            kind = kinds[0]
            message = (
                f'Expected token {kind.name}, '
                f'but found {self.cur_token.kind.name} '
                f'at {self.cur_token.loc}.'
            )
        else:
            message = ''
        self.error(message)

    def eat(self) -> None:
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.cur_token = self.tokens[self.token_index]
        else:
            self.error('Unexpected end of file.')

    @property
    def next_token(self) -> Token:
        if self.token_index + 1 < len(self.tokens):
            return self.tokens[self.token_index]
        elif self.token_index + 1 == len(self.tokens):
            self.error(f'Unexpected end of file at {self.cur_token}')
        else:
            self.error('Unexpected end of file')

    def eat_expecting(self, *kinds: TokenKind) -> None:
        self.eat()
        if self.cur_token.kind not in {*kinds}:
            self.error_expecting(*kinds)

    def expect_and_eat(self, *kinds: TokenKind) -> None:
        if self.cur_token.kind not in {*kinds}:
            self.error_expecting(*kinds)
        self.eat()

    def expect(self, *kinds: TokenKind) -> None:
        if self.cur_token.kind not in {*kinds}:
            self.error_expecting(*kinds)

    def eat_newlines_expecting_at_least_one(self) -> None:
        self.expect_and_eat(TokenKind.NEWLINE)
        while self.cur_token.kind == TokenKind.NEWLINE:
            self.eat()

    def eat_any_newlines(self) -> None:
        while self.cur_token.kind == TokenKind.NEWLINE:
            self.eat()

    @staticmethod
    def assume_lexeme(lexeme: Optional[str]) -> str:
        assert lexeme is not None, (
            f'found {TokenKind.NAME.name} token with no lexeme'
        )
        return lexeme

    @property
    def at_definition(self) -> bool:
        return (
            self.cur_token.kind == TokenKind.NAME and
            self.cur_token.lexeme in {TRANSFORM, TEST}
        )

    def parse(self) -> Module:
        self.eat()
        module = self.parse_module()
        return module

    def parse_module(self) -> Module:
        definitions: List[Definition] = []
        while self.at_definition:
            definition = self.parse_definition()
            definitions.append(definition)
        self.expect(TokenKind.EOF)
        return Module(definitions)

    def parse_definition(self) -> Definition:
        if self.cur_token.lexeme == TRANSFORM:
            transform = self.parse_transform()
            return transform
        elif self.cur_token.lexeme == TEST:
            test = self.parse_test()
            return test
        assert 0, 'should be at a definition'

    def parse_transform(self) -> Transform:
        self.expect_and_eat(TokenKind.NAME)
        lexeme = self.assume_lexeme(self.cur_token.lexeme)
        if lexeme in RESERVED_NAMES:
            self.error(
                f'Name {lexeme} is a reserved word an cannot be used as a '
                'Transform name'
            )
        self.expect_and_eat(TokenKind.NAME)
        self.eat_any_newlines()
        self.expect_and_eat(TokenKind.LBRACKET)
        self.eat_any_newlines()
        rule_blocks: List[RuleBlock] = []
        while self.cur_token.kind != TokenKind.RBRACKET:
            rule_block = self.parse_rule_block()
            rule_blocks.append(rule_block)
        self.eat_any_newlines()
        self.expect_and_eat(TokenKind.RBRACKET)
        self.eat_any_newlines()
        return Transform(Name(lexeme), rule_blocks)

    def parse_test(self) -> Test:
        # TODO
        return Test()

    def parse_rule_block(self) -> RuleBlock:
        self.expect(TokenKind.NAME)
        rule_kind = self.cur_token.lexeme
        rule_block: RuleBlock
        if rule_kind == ALIASES:
            rule_block = self.parse_alias_block()
        elif rule_kind == HEADERS:
            rule_block = self.parse_header_block()
        elif rule_kind == VALUES:
            rule_block = self.parse_value_block()
        else:
            self.error(
                f'Expected {ALIASES}, {HEADERS}, or {VALUES}, '
                f'but found {rule_kind}'
            )
        return rule_block

    def parse_alias_block(self) -> AliasBlock:
        # TODO
        return AliasBlock([])

    def parse_header_block(self) -> HeaderBlock:
        self.expect_and_eat(TokenKind.NAME)
        self.eat_any_newlines()
        self.expect_and_eat(TokenKind.LBRACKET)
        self.eat_any_newlines()
        header_rules: List[HeaderRule] = []
        while self.cur_token.kind != TokenKind.RBRACKET:
            header_rule = self.parse_header_rule()
            header_rules.append(header_rule)
        self.eat_any_newlines()
        self.expect_and_eat(TokenKind.RBRACKET)
        self.eat_any_newlines()
        return HeaderBlock([])

    def parse_value_block(self) -> ValueBlock:
        # TODO
        return ValueBlock([])

    def parse_header_rule(self) -> HeaderRule:
        header = self.parse_header()
        self.expect_and_eat(TokenKind.ARROW)
        pipeline = self.parse_execution()
        self.eat_newlines_expecting_at_least_one()
        return HeaderRule(header, pipeline)

    def parse_header(self) -> Header:
        # TODO for now just assume String
        #      in the future we will have to peek
        string = self.parse_string()
        return string

    def parse_rvalue(self) -> RValue:
        # TODO
        ...

    def parse_execution(self) -> Pipeline:
        # TODO for now just assume String
        #      in the future we will have to peek
        operations: List[Operation] = []
        string = self.parse_string()
        operations.append(string)
        return Pipeline(operations)

    def parse_string(self) -> String:
        self.expect(TokenKind.STRING)
        lexeme = self.assume_lexeme(self.cur_token.lexeme)
        self.eat()
        return String(lexeme)
