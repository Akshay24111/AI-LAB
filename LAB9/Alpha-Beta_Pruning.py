
def alpha_beta(node, depth, alpha, beta, maximizing_player):

    # Leaf node
    if depth == 0 or isinstance(node, int):
        return node

    if maximizing_player:
        value = float('-inf')

        for child in node:
            value = max(
                value,
                alpha_beta(child, depth - 1,
                           alpha, beta, False)
            )

            alpha = max(alpha, value)

            # Alpha-Beta pruning
            if alpha >= beta:
                break

        return value

    else:
        value = float('inf')

        for child in node:
            value = min(
                value,
                alpha_beta(child, depth - 1,
                           alpha, beta, True)
            )

            beta = min(beta, value)

            # Alpha-Beta pruning
            if alpha >= beta:
                break

        return value


# Game tree
tree = [
    [3, 5],
    [6, 9],
    [1, 2]
]

result = alpha_beta(
    tree,
    2,
    float('-inf'),
    float('inf'),
    True
)

print("Optimal value:", result)
