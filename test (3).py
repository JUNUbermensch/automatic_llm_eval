import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset

class CustomDataset(Dataset):
    def __init__(self, dataset_name, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        
        if dataset_name == 'squad':
            squad_data = load_dataset("rajpurkar/squad_v2")
            for item in squad_data['train']:
                context = item['context']
                question = item['question']
                answer = item['answers']['text'][0] if item['answers']['text'] else 'No answer provided'
                self.data.append({
                    "input_text": f"question: {question} context: {context}",
                    "target_text": answer
                })
        elif dataset_name == 'klue':
            klue_data = load_dataset("klue", "mrc")
            for item in klue_data['train']:
                context = item['context']
                question = item['question']
                answer = item['answers']['text'][0] if item['answers']['text'] else 'No answer'  # Handling no answer case
                self.data.append({
                    "input_text": f"question: {question} context: {context}",
                    "target_text": answer
                })

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        source_encoded = self.tokenizer(
            sample['input_text'],
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        target_encoded = self.tokenizer(
            sample['target_text'],
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        return source_encoded.input_ids.squeeze(0), target_encoded.input_ids.squeeze(0)

model_name = 'wisenut-nlp-team/t5-fid-new'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Choose dataset here: 'squad' or 'klue'
chosen_dataset = 'klue'
dataset = CustomDataset(chosen_dataset, tokenizer)
data_loader = DataLoader(dataset, batch_size=10)

def evaluate(model, data_loader):
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    total_f1 = 0
    total_em = 0
    total_count = 0
    
    for input_ids, labels in data_loader:
        input_ids = input_ids.to(device)
        labels = labels.to(device)
        with torch.no_grad():
            outputs = model.generate(input_ids)
            decoded_outputs = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
            print(decoded_outputs)

    return {"F1": total_f1 / total_count, "EM": total_em / total_count}

results = evaluate(model, data_loader)
print(f"F1 Score: {results['F1']}, Exact Match: {results['EM']}")
