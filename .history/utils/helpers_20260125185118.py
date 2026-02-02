def calculate_accuracy(detected_order, target_order):
    """
    Accuracy is based STRICTLY on order comparison.
    """

    target_len = len(target_order)
    detected_len = len(detected_order)

    correct = 0

    for i in range(min(target_len, detected_len)):
        if detected_order[i] == target_order[i]:
            correct += 1

    wrong = detected_len - correct
    missing = max(0, target_len - detected_len)

    # 🔥 CRITICAL FIX
    if detected_order == target_order:
        accuracy = 100.0
    else:
        accuracy = round((correct / target_len) * 100, 2)

    return correct, wrong, missing, accuracy