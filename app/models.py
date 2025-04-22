import json

# #------------------Логика работы с SentenceTransformer
# def process_embedding(text, output_path):
#     embedding = model.encode(text)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump({
#             "embedding": embedding.tolist()
#         }, f, ensure_ascii=False, indent=4)
#     return output_path

# def process_embedding(text, output_path):
#     # embedding = model.encode(text)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump({
#             "embedding": text.tolist()
#         }, f, ensure_ascii=False, indent=4)
#     return output_path
