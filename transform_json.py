import json
import re
import os

def generate_id(text):
    text = text.lower()
    text = re.sub(r'\s+specs$', '', text)
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def transform():
    try:
        with open('full_car_tree.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except FileNotFoundError:
        print("Ошибка: full_car_tree.json не найден.")
        return

    # Создаем папку для брендов, если её нет
    output_dir = 'brands'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    brand_dict = []
    themes_children = []

    for item in old_data:
        brand_name = item.get('brand', 'Unknown')
        brand_id = generate_id(brand_name)
        
        # 1. Данные для основного словаря
        brand_dict.append({"id": brand_id, "title": brand_name})

        # 2. Формируем вложенную структуру для отдельного файла бренда
        brand_tree = {
            "id": f"brand_{brand_id}",
            "title": brand_name,
            "models": []
        }

        for model in item.get('models', []):
            model_name = model.get('model', 'Unknown')
            model_node = {
                "id": f"model_{generate_id(model_name)}",
                "title": model_name,
                "generations": []
            }

            for gen in model.get('generations', []):
                gen_name = gen.get('generation', 'Unknown')
                gen_node = {
                    "id": f"gen_{generate_id(gen_name)}",
                    "title": gen_name,
                    "children": []
                }

                unique_mods = sorted(list(set(gen.get('modifications', []))))
                for mod in unique_mods:
                    mod_title = mod.replace(' specs', '').strip()
                    gen_node["children"].append({
                        "id": f"mod_{generate_id(mod)}",
                        "title": mod_title
                    })
                
                model_node["generations"].append(gen_node)
            
            brand_tree["models"].append(model_node)

        # Сохраняем отдельный файл для бренда (например, brands/audi.json)
        brand_file_path = f"{output_dir}/{brand_id}.json"
        with open(brand_file_path, 'w', encoding='utf-8') as f:
            json.dump(brand_tree, f, ensure_ascii=False, indent=2)

        # 3. В главный файл пишем только "заглушку" со ссылкой
        themes_children.append({
            "id": f"brand_{brand_id}",
            "title": brand_name,
            "refs": ["car_brands"],
            "url": f"/static/brands/{brand_id}.json" # Путь, по которому фронт будет дергать файл
        })

    # Главный файл (индекс)
    index_schema = {
        "schema_version": "2.1",
        "dictionaries": {
            "car_brands": brand_dict
        },
        "themes": [
            {
                "id": "cars_catalog",
                "title": "Каталог автомобилей",
                "children": themes_children
            }
        ]
    }

    with open('schema_index.json', 'w', encoding='utf-8') as f:
        json.dump(index_schema, f, ensure_ascii=False, indent=2)
    
    print(f"Готово! Создана папка '{output_dir}' с {len(brand_dict)} файлами.")
    print(f"Создан индексный файл: schema_index.json")

if __name__ == "__main__":
    transform()