import numpy as np
from scipy.optimize import minimize_scalar


class IRTEngine:
    """Item Response Theory calculation engine using 3PL model."""

    # ---------- PROBABILITY ----------
    @staticmethod
    def probability(theta, a, b, c):
        exponent = -a * (theta - b)
        return c + (1 - c) / (1 + np.exp(exponent))

    # ---------- INFORMATION ----------
    @staticmethod
    def information(theta, a, b, c):
        p = IRTEngine.probability(theta, a, b, c)
        q = 1 - p
        return (a ** 2 * p * q) / ((1 - c) ** 2)

    # ---------- LOG LIKELIHOOD ----------
    @staticmethod
    def log_likelihood(theta, answer_pattern, questions):
        ll = 0.0

        for is_correct, q in zip(answer_pattern, questions):
            p = IRTEngine.probability(
                theta,
                q.discrimination_a,
                q.difficulty_b,
                q.guessing_c
            )

            p = np.clip(p, 1e-10, 1 - 1e-10)

            ll += np.log(p) if is_correct else np.log(1 - p)

        return -ll

    # ---------- THETA ESTIMATION ----------
    @classmethod
    def estimate_theta(cls, answer_pattern, questions, bounds=(-4, 4)):
        if not answer_pattern:
            return {"theta": 0.0, "se": 1.0, "converged": False}

        result = minimize_scalar(
            lambda t: cls.log_likelihood(t, answer_pattern, questions),
            bounds=bounds,
            method="bounded"
        )

        theta_hat = result.x

        total_info = sum(
            cls.information(
                theta_hat,
                q.discrimination_a,
                q.difficulty_b,
                q.guessing_c
            )
            for q in questions
        )

        se = 1 / np.sqrt(total_info) if total_info > 0 else 1.0

        return {
            "theta": theta_hat,
            "se": se,
            "converged": result.success
        }

    # ---------- QUESTION SELECTION ----------
    @classmethod
    def select_next_question(cls, current_theta, available_questions):
        max_info = -1
        best_question = None

        for q in available_questions:
            info = cls.information(
                current_theta,
                q.discrimination_a,
                q.difficulty_b,
                q.guessing_c
            )
            if info > max_info:
                max_info = info
                best_question = q

        return best_question
