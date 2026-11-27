import re

# ---------- 1. PARSER ----------

def tokenize(s):
    pattern = r'<->|->|[A-Za-z_]\w*|[()&,|~.]'
    tokens = re.findall(pattern, s)
    if ''.join(tokens).replace(' ', '') != re.sub(r'\s+', '', s):
        raise ValueError("Invalid expression")
    return tokens


class Parser:
    def __init__(self, text):
        self.t = tokenize(text)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self):
        x = self.peek()
        if x is None:
            raise ValueError("Unexpected end of input")
        self.i += 1
        return x

    def parse(self):
        result = self.iff()
        if self.peek() is not None:
            raise ValueError("Unexpected token: " + self.peek())
        return result

    def iff(self):
        x = self.imp()
        while self.peek() == '<->':
            self.take()
            x = ('iff', x, self.imp())
        return x

    def imp(self):
        x = self.disjunction()
        if self.peek() == '->':
            self.take()
            x = ('imp', x, self.imp())
        return x

    def disjunction(self):
        x = self.conjunction()
        while self.peek() == '|':
            self.take()
            x = ('or', x, self.conjunction())
        return x

    def conjunction(self):
        x = self.unary()
        while self.peek() == '&':
            self.take()
            x = ('and', x, self.unary())
        return x

    def unary(self):
        t = self.peek()

        if t == '~':
            self.take()
            return ('not', self.unary())

        if t in ('forall', 'exists'):
            op = self.take()
            var = self.take()
            self.take()  # dot
            return (op, var, self.iff())

        if t == '(':
            self.take()
            x = self.iff()
            self.take()  # closing parenthesis
            return x

        name = self.take()
        args = []

        if self.peek() == '(':
            self.take()
            args.append(self.take())
            while self.peek() == ',':
                self.take()
                args.append(self.take())
            self.take()  # closing parenthesis

        return ('atom', name, args)


# ---------- 2. ELIMINATE IMPLICATION ----------

def eliminate_implications(e):
    op = e[0]

    if op == 'atom':
        return e

    if op == 'not':
        return ('not', eliminate_implications(e[1]))

    if op in ('forall', 'exists'):
        return (op, e[1], eliminate_implications(e[2]))

    a = eliminate_implications(e[1])
    b = eliminate_implications(e[2])

    if op == 'imp':
        return ('or', ('not', a), b)

    if op == 'iff':
        return (
            'and',
            ('or', ('not', a), b),
            ('or', ('not', b), a)
        )

    return (op, a, b)


# ---------- 3. MOVE NEGATIONS INWARD ----------

def nnf(e, neg=False):
    op = e[0]

    if op == 'atom':
        return ('not', e) if neg else e

    if op == 'not':
        return nnf(e[1], not neg)

    if op in ('forall', 'exists'):
        new_op = op
        if neg:
            new_op = 'exists' if op == 'forall' else 'forall'
        return (new_op, e[1], nnf(e[2], neg))

    if op in ('and', 'or'):
        new_op = op
        if neg:
            new_op = 'or' if op == 'and' else 'and'
        return (new_op, nnf(e[1], neg), nnf(e[2], neg))

    raise ValueError("Unexpected operator")


# ---------- 4. STANDARDIZE VARIABLES ----------

counter = 0

def substitute(e, mapping):
    op = e[0]

    if op == 'atom':
        return ('atom', e[1],
                [mapping.get(x, x) for x in e[2]])

    if op == 'not':
        return ('not', substitute(e[1], mapping))

    if op in ('and', 'or'):
        return (op, substitute(e[1], mapping),
                substitute(e[2], mapping))

    if op in ('forall', 'exists'):
        return (op, e[1], substitute(e[2], mapping))

    return e


def standardize(e, mapping=None):
    global counter

    if mapping is None:
        mapping = {}

    op = e[0]

    if op == 'atom':
        return substitute(e, mapping)

    if op == 'not':
        return ('not', standardize(e[1], mapping))

    if op in ('and', 'or'):
        return (op, standardize(e[1], mapping),
                standardize(e[2], mapping))

    if op in ('forall', 'exists'):
        counter += 1
        new_var = '_v' + str(counter)

        new_mapping = mapping.copy()
        new_mapping[e[1]] = new_var

        return (op, new_var, standardize(e[2], new_mapping))

    return e


# ---------- 5. PRENEX NORMAL FORM ----------

def prenex(e):
    op = e[0]

    if op in ('forall', 'exists'):
        p, matrix = prenex(e[2])
        return [(op, e[1])] + p, matrix

    if op in ('and', 'or'):
        p1, a = prenex(e[1])
        p2, b = prenex(e[2])
        return p1 + p2, (op, a, b)

    return [], e


# ---------- 6. SKOLEMIZATION ----------

def skolemize(prefix, matrix):
    universals = []
    skolem_count = 0

    for op, var in prefix:
        if op == 'forall':
            universals.append(var)

        else:
            skolem_count += 1

            if universals:
                skolem = "sk" + str(skolem_count) + "(" + ",".join(universals) + ")"
            else:
                skolem = "sk" + str(skolem_count)

            matrix = substitute(matrix, {var: skolem})

    return matrix


# ---------- 7. DISTRIBUTE OR OVER AND ----------

def distribute(a, b):
    if a[0] == 'and':
        return (
            'and',
            distribute(a[1], b),
            distribute(a[2], b)
        )

    if b[0] == 'and':
        return (
            'and',
            distribute(a, b[1]),
            distribute(a, b[2])
        )

    return ('or', a, b)


def to_cnf(e):
    op = e[0]

    if op == 'atom' or op == 'not':
        return e

    if op == 'and':
        return ('and', to_cnf(e[1]), to_cnf(e[2]))

    if op == 'or':
        a = to_cnf(e[1])
        b = to_cnf(e[2])
        return distribute(a, b)

    return e


# ---------- 8. PRINT RESULT ----------

def display(e):
    op = e[0]

    if op == 'atom':
        if e[2]:
            return e[1] + '(' + ','.join(e[2]) + ')'
        return e[1]

    if op == 'not':
        return '~' + display(e[1])

    if op in ('and', 'or'):
        symbol = '&' if op == 'and' else '|'
        return '(' + display(e[1]) + ' ' + symbol + ' ' + display(e[2]) + ')'

    return str(e)


# ---------- MAIN PROGRAM ----------

def fol_to_cnf(formula):
    global counter
    counter = 0

    e = Parser(formula).parse()

    e = eliminate_implications(e)
    e = nnf(e)
    e = standardize(e)

    prefix, matrix = prenex(e)

    matrix = skolemize(prefix, matrix)

    result = to_cnf(matrix)

    return display(result)


# ---------- INPUT AND OUTPUT ----------

print("FOL TO CNF CONVERSION")
print("Use: forall, exists, &, |, ~, ->, <->")
formula = input("Enter FOL expression: ")

try:
    result = fol_to_cnf(formula)
    print("CNF:", result)
except Exception as error:
    print("Error:", error)
