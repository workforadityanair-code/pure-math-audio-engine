import math
import random

class BareMetalNeuralCounterpoint:
    """2-layer MLP for modal counterpoint conditioned on cantus firmus."""

    def __init__(self, input_dim: int = 8, hidden_dim: int = 16, output_dim: int = 8):
        self.w1 = [[(random.random() - 0.5) * 0.2 for _ in range(hidden_dim)] for _ in range(input_dim)]
        self.b1 = [0.0] * hidden_dim
        self.w2 = [[(random.random() - 0.5) * 0.2 for _ in range(output_dim)] for _ in range(hidden_dim)]
        self.b2 = [0.0] * output_dim

    @staticmethod
    def _relu(x: float) -> float:
        return max(0.0, x)

    @staticmethod
    def _relu_grad(x: float) -> float:
        return 1.0 if x > 0.0 else 0.0

    @staticmethod
    def _softmax(vec: list[float]) -> list[float]:
        shift_vec = [v - max(vec) for v in vec]
        exp_vec = [math.exp(v) for v in shift_vec]
        s = sum(exp_vec) + 1e-12
        return [v / s for v in exp_vec]

    def forward(self, x: list[float]) -> tuple[list[float], list[float]]:
        h = [sum(x[j] * self.w1[j][k] for j in range(len(x))) + self.b1[k] for k in range(len(self.b1))]
        h_act = [self._relu(v) for v in h]
        out = [sum(h_act[k] * self.w2[k][m] for k in range(len(h_act))) + self.b2[m] for m in range(len(self.b2))]
        probs = self._softmax(out)
        return h_act, probs

    def train_step(self, x: list[float], target_idx: int, lr: float = 0.05) -> None:
        h_act, probs = self.forward(x)

        d_out = list(probs)
        d_out[target_idx] -= 1.0

        for k in range(len(self.w2)):
            for m in range(len(self.b2)):
                self.w2[k][m] -= lr * d_out[m] * h_act[k]
        for m in range(len(self.b2)):
            self.b2[m] -= lr * d_out[m]

        d_hidden = [0.0] * len(self.b1)
        for k in range(len(self.b1)):
            err = sum(d_out[m] * self.w2[k][m] for m in range(len(self.b2)))
            d_hidden[k] = err * self._relu_grad(h_act[k])

        for j in range(len(self.w1)):
            for k in range(len(self.b1)):
                self.w1[j][k] -= lr * d_hidden[k] * x[j]
        for k in range(len(self.b1)):
            self.b1[k] -= lr * d_hidden[k]