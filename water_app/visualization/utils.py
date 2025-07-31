def select_meter(df):
    """Выбор конкретного счетчика из списка"""
    meters = df['ManagedObjectid'].unique()

    print("\nДоступные счетчики:")
    for i, meter in enumerate(meters, 1):
        print(f"{i}. {meter}")

    while True:
        try:
            choice = input("Выберите счетчик (номер или ID, 0 - отмена): ").strip()
            if choice == '0':
                return None

            # Пробуем интерпретировать как номер
            if choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(meters):
                    return meters[choice_idx]

            # Пробуем интерпретировать как ID
            if choice in meters:
                return choice

            print("Некорректный ввод. Попробуйте снова.")
        except:
            print("Некорректный ввод. Попробуйте снова.")


def get_date_input():
    """Получает от пользователя диапазон дат"""
    print("\n=== ФИЛЬТР ПО ДАТЕ ===")
    start = input("Начальная дата (YYYY-MM-DD или Enter для начала данных): ").strip() or None
    end = input("Конечная дата (YYYY-MM-DD или Enter для конца данных): ").strip() or None
    return start, end


def get_meter_input(available_meters):
    """Получает от пользователя номера счетчиков"""
    print("\n=== ФИЛЬТР ПО СЧЕТЧИКАМ ===")
    print(f"Доступно {len(available_meters)} счетчиков.")

    print("\nВарианты ввода:")
    print("1. Один счетчик - введите ID")
    print("2. Несколько счетчиков - введите ID через запятую")
    print("3. Все счетчики - нажмите Enter или введите 'all'")

    user_input = input("Ваш выбор: ").strip()

    if not user_input or user_input.lower() == 'all':
        return None

    return [mid.strip() for mid in user_input.split(',')]


def get_city_input(available_cities):
    """Получает от пользователя названия городов"""
    print("\n=== ФИЛЬТР ПО ГОРОДУ ===")
    if available_cities.size > 0:
        print(f"Доступные города: {', '.join(available_cities)}")
    else:
        print("Данные о городах отсутствуют.")
        return None

    print("\nВарианты ввода:")
    print("1. Один город - введите название")
    print("2. Несколько городов - введите названия через запятую")
    print("3. Все города - нажмите Enter или введите 'all'")

    user_input = input("Ваш выбор: ").strip()

    if not user_input or user_input.lower() == 'all':
        return None

    return [city.strip() for city in user_input.split(',')]


def get_meter_type_input(available_types):
    """Получает от пользователя типы счетчиков"""
    print("\n=== ФИЛЬТР ПО ТИПУ СЧЕТЧИКА ===")
    if available_types.size > 0:
        print(f"Доступные типы счетчиков: {', '.join(available_types)}")
    else:
        print("Данные о типах счетчиков отсутствуют.")
        return None

    print("\nВарианты ввода:")
    print("1. Pulse1 - импульсные счетчики")
    print("2. Pulse1_Total - счетчики с общим потреблением")
    print("3. Все типы - нажмите Enter или введите 'all'")

    user_input = input("Ваш выбор: ").strip()

    if not user_input or user_input.lower() == 'all':
        return None

    return [mt.strip() for mt in user_input.split(',')]
