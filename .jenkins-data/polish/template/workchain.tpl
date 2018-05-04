class ${class_name}(WorkChain):

    ERROR_NO_JOB_CALCULATION = 1
    ERROR_NO_OUTPUT_NODE = 2

    @classmethod
    def define(cls, spec):
        super(${class_name}, cls).define(spec)
        spec.input('code', valid_type=Code, required=False)
        spec.input('operands', valid_type=Str)
        spec.outline(
${outline}
        )
        spec.output('result', valid_type=Int)

    def setup(self):
        self.ctx.child_class = ${child_class}
        self.ctx.result = Int(0)
        self.ctx.operands = [int(i) for i in self.inputs.operands.value.split(' ')]
        self.ctx.workchains = []
        self.ctx.iterators = []
        self.ctx.iterators_sign = []
        self.ctx.iterators_stack = []
        self.report('Initial operands {}'.format(self.ctx.operands))

    def pre_iterate(self):
        self.ctx.iterators_stack.append(deepcopy(self.ctx.operands))
        iterator = self.ctx.operands.pop(0)
        self.ctx.iterators.append(abs(iterator))
        if iterator >= 0:
            self.ctx.iterators_sign.append(1)
        else:
            self.ctx.iterators_sign.append(-1)

    def iterate(self):
        if self.ctx.iterators[-1] == 0:
            self.ctx.iterators.pop()
            self.ctx.iterators_sign.pop()
            self.ctx.operands = self.ctx.iterators_stack.pop()
            return False
        else:
            self.ctx.iterators[-1] -= 1
            full_stack = deepcopy(self.ctx.iterators_stack[-1])
            self.ctx.operands = full_stack[1:]
            return True

    def is_positive(self):
        return self.ctx.operands[0] >= 0

    def add(self):
        operand = self.ctx.operands.pop(0)
        self.report('summing the inputs {} and {}'.format(self.ctx.result, operand))
        self.ctx.result = self.ctx.result + abs(operand) * prod(self.ctx.iterators_sign)

    def subtract(self):
        operand = self.ctx.operands.pop(0)
        self.report('subtracting the inputs {} and {}'.format(self.ctx.result, operand))
        self.ctx.result = self.ctx.result - abs(operand) * prod(self.ctx.iterators_sign)

    def add_calculation(self):
        operand = self.ctx.operands.pop(0)
        operand = abs(operand) * prod(self.ctx.iterators_sign)
        inputs = {
            'code': self.inputs.code,
            'x': self.ctx.result,
            'y': Int(operand),
            'options': get_default_options(),
        }

        running = self.submit(ArithmeticAddCalculation, **inputs)
        self.report('launching {}<{}> with inputs {} and {}'.format(ArithmeticAddCalculation.__name__, running.pk, self.ctx.result, operand))

        return ToContext(calculations=append_(running))

    def post_add(self):
        try:
            calculation = self.ctx.calculations[-1]
        except (AttributeError, IndexError) as exception:
            self.report('no job calculation found')
            return self.ERROR_NO_JOB_CALCULATION

        try:
            self.ctx.result = calculation.out.sum
        except AttributeError as exception:
            self.report('no output node found')
            return self.ERROR_NO_OUTPUT_NODE

    def add_workfunction(self):
        operand = self.ctx.operands.pop(0)
        operand = abs(operand) * prod(self.ctx.iterators_sign)
        self.report('running add workfunction with inputs {} and {}'.format(self.ctx.result.value, operand))
        self.ctx.result = subtract(self.ctx.result, Int(operand))

    def subtract_workfunction(self):
        operand = self.ctx.operands.pop(0)
        operand = abs(operand) * prod(self.ctx.iterators_sign)
        self.report('running subtract workfunction with inputs {} and {}'.format(self.ctx.result.value, operand))
        self.ctx.result = subtract(self.ctx.result, Int(operand))

    def raise_power(self):
        operand = self.ctx.operands.pop(0)
        operands = Str(' '.join([str(o) for o in self.ctx.operands]))

        inputs = {
            'operands': operands,
        }

        if 'code' in self.inputs:
            inputs['code'] = self.inputs.code

        for i in range(operand):
            running = self.submit(self.ctx.child_class, **inputs)
            self.report('launching {}<{}> with operands {}'.format(self.ctx.child_class.__name__, running.pk, operands.value))          
            self.to_context(workchains=append_(running))

    def post_raise_power(self):
        results = []
        for workchain in self.ctx.workchains:
            results.append(workchain.out.result.value)

        self.ctx.workchains = []
        self.ctx.result += Int(prod(results) * prod(self.ctx.iterators_sign))

    def results(self):
        if not isinstance(self.ctx.result, Int):
            self.ctx.result = Int(self.ctx.result)

        self.report('Workchain finished with result {}'.format(self.ctx.result.value))
        self.out('result', self.ctx.result)
