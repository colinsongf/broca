from itertools import product
from broca.pipeline.cryo import Cryo
from broca.pipeline.pipe import PipeType


class Pipeline():
    def __init__(self, *pipes, **kwargs):
        self.freeze = kwargs.get('freeze', True)
        self.refresh = kwargs.get('refresh', False)
        self.cryo = Cryo(refresh=self.refresh)

        # If any of the pipes is a list or a multi-pipeline, we are building multiple pipelines
        if any(isinstance(p, list) or self._is_multi(p) for p in pipes):
            # Coerce all pipes to lists
            c_pipes = []
            for p in pipes:
                if isinstance(p, list):
                    c_pipes.append(p)
                elif self._is_multi(p):
                    c_pipes.append(p.pipelines)
                else:
                    c_pipes.append([p])

            # Build each pipeline
            self.pipelines = [Pipeline(*pipes_) for pipes_ in product(*c_pipes)]

        else:
            self.pipes = pipes

            # Validate the pipeline
            for p_out, p_in in zip(pipes, pipes[1:]):
                if isinstance(p_out, tuple):
                    output = tuple(p.output for p in p_out)
                else:
                    output = p_out.output

                if isinstance(p_in, tuple):
                    input = tuple(p.input for p in p_in)

                    # If the output is not a tuple,
                    # we are replicating it across each branch (one-to-branch)
                    if not isinstance(output, tuple):
                        output = tuple(output for i in input)
                else:
                    input = p_in.input

                if output != input:
                    raise Exception('Incompatible: pipe <{}> outputs <{}>, pipe <{}> requires input of <{}>.'.format(
                        # Hmm this could be cleaner...
                        type(p_out).__name__ if not isinstance(p_out, tuple) else tuple(type(p).__name__ for p in p_out),
                        output.name if isinstance(output, PipeType) else tuple(t.name for t in output),
                        type(p_in).__name__ if not isinstance(p_in, tuple) else tuple(type(p).__name__ for p in p_in),
                        input.name if isinstance(input, PipeType) else tuple(t.name for t in input)
                    ))

            # So pipelines can be nested
            first = self.pipes[0]
            last = self.pipes[-1]
            self.input = first.input if not isinstance(first, tuple) else tuple(p.input for p in first)
            self.output = last.input if not isinstance(last, tuple) else tuple(p.input for p in last)

    def _is_multi(self, pipe):
        return isinstance(pipe, Pipeline) and hasattr(pipe, 'pipelines')

    def __call__(self, input):
        if hasattr(self, 'pipelines'):
            return tuple(p(input) for p in self.pipelines)
        else:
            for pipe in self.pipes:
                # Branch
                if isinstance(pipe, tuple):
                    # Multi-to-branch/branch-to-branch
                    if isinstance(input, tuple):
                        output = tuple(self.cryo(p, i) if self.freeze else p(i) for p, i in zip(pipe, input))

                    # One-to-branch
                    else:
                        output = tuple(self.cryo(p, input) if self.freeze else p(input) for p in pipe)
                else:
                    if isinstance(input, tuple):
                        output = self.cryo(pipe, *input) if self.freeze else pipe(*input)
                    else:
                        output = self.cryo(pipe, input) if self.freeze else pipe(input)
                input = output
            return output

    def __repr__(self):
        if hasattr(self, 'pipelines'):
            return 'MultiPipeline: {}'.format(' || '.join([str(p) for p in self.pipelines]))
        else:
            return ' -> '.join([str(p) for p in self.pipes])
