import json


def get_dashboard_context():
    original_labels = ["PIN-код", "SMS-код", "CVV", "Блокировка", "Журналирование"]
    original_values = [14.25, 9.00, 7.40, 12.10, 10.30]

    enhanced_labels = ["PIN-код", "SMS-код", "CVV", "Блокировка", "Журналирование"]
    enhanced_values = [17.10, 10.80, 8.60, 15.20, 13.90]

    attempts_labels = ["Устройство A", "Устройство B", "Устройство C", "Устройство D"]
    attempts_values = [1, 3, 2, 4]

    return {
        "total_operations": 7,
        "max_risk": 17.10,
        "critical_count": 4,

        "original_table": """
        <table>
            <tr>
                <th>Операция</th>
                <th>R</th>
            </tr>
            <tr>
                <td>Проверить PIN-код</td>
                <td>14.25</td>
            </tr>
            <tr>
                <td>Проверить SMS-код</td>
                <td>9.00</td>
            </tr>
            <tr>
                <td>Проверить CVV</td>
                <td>7.40</td>
            </tr>
            <tr>
                <td>Блокировка</td>
                <td>12.10</td>
            </tr>
            <tr>
                <td>Журналирование</td>
                <td>10.30</td>
            </tr>
        </table>
        """,

        "enhanced_table": """
        <table>
            <tr>
                <th>Операция</th>
                <th>R</th>
            </tr>
            <tr>
                <td>Проверить PIN-код</td>
                <td>17.10</td>
            </tr>
            <tr>
                <td>Проверить SMS-код</td>
                <td>10.80</td>
            </tr>
            <tr>
                <td>Проверить CVV</td>
                <td>8.60</td>
            </tr>
            <tr>
                <td>Блокировка</td>
                <td>15.20</td>
            </tr>
            <tr>
                <td>Журналирование</td>
                <td>13.90</td>
            </tr>
        </table>
        """,

        "original_labels_json": json.dumps(original_labels, ensure_ascii=False),
        "original_values_json": json.dumps(original_values, ensure_ascii=False),

        "enhanced_labels_json": json.dumps(enhanced_labels, ensure_ascii=False),
        "enhanced_values_json": json.dumps(enhanced_values, ensure_ascii=False),

        "attempts_labels_json": json.dumps(attempts_labels, ensure_ascii=False),
        "attempts_values_json": json.dumps(attempts_values, ensure_ascii=False),
    }