def reorder_for_context(ranked):
    """Place the strongest items at the edges of the context, the weakest in the middle.

    Input is best-first. Ranks 1, 3, 5, ... fill from the front; ranks 2, 4, ... fill from
    the back. Ranked [1, 2, 3, 4, 5] becomes [1, 3, 5, 4, 2]:
    best first, second-best last, weakest in the middle.
    """
    front, back = [], []
    for i, item in enumerate(ranked):
        (front if i % 2 == 0 else back).append(item)
    return front + back[::-1]