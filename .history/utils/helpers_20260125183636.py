def calculate_accuracy(detected, target):
    correct = 0
    for i in range(min(len(detected), len(target))):
        if detected[i] == target[i]:
            correct += 1

    wrong = len(detected) - correct
    missing = max(0, len(target) - len(detected))
    accuracy = round((correct / len(target)) * 100, 2)

    return correct, wrong, missing, accuracy