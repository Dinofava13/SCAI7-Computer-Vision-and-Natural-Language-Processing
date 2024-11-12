# -*- coding: utf-8 -*-
"""03-Tim 8-4.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GLtx1ieyvYi3OmVlrgXXqgyoBlEpzUwp

# Assignment Chapter 3 - NLP [Case #4]
Startup Campus, Indonesia - `Artificial Intelligence (AI)` (Batch 7)
* Type: **NATURAL LANGUAGE UNDERSTANDING (NLU)**
* Dataset: Disaster Tweets
* Libraries: NLTK, Pandas, Numpy, Scikit-learn, PyTorch, Transformers
* Objective: Text Classification with Bidirectional Encoder Representation for Transformers (BERT)

`PERSYARATAN` Semua modul (termasuk versi yang sesuai) sudah di-install dengan benar.
<br>`CARA PENGERJAAN` Lengkapi baris kode yang ditandai dengan **#TODO**.
<br>`TARGET PORTFOLIO` Peserta mampu mengklasifikasikan teks dengan menggunakan model pre-trained BERT.
<br>`PERHATIAN` Mohon untuk **TIDAK** mengubah code apapun di dalam **UDFs**.

### Case Study
Dengan ketersediaan *smartphone* yang semakin luas, masyarakat dapat melaporkan kejadian darurat yang mereka saksikan secara *real-time* melalui platform X (dahulu Twitter). Hal ini membuat berbagai lembaga, seperti organisasi bantuan bencana dan agensi berita, semakin tertarik untuk memantau X secara sistematis.

Sebagai seorang *AI Scientist*, Anda ditugaskan untuk mengklasifikasikan *disaster tweet*, yaitu apakah teks di platform X merupakan sebuah laporan tidak langsung mengenai bencana tertentu. Model BERT (singkatan dari *Bidirectional Encoder Representations for Transformers*) dapat digunakan untuk menyelesaikan kasus ini. Dengan mengimplementasikan teknik *fine-tuning*, model yang Anda buat dapat membawa manfaat kedepan untuk:
- Menganalisis pola komunikasi dan respon masyarakat dalam situasi darurat.
- Mengembangkan sistem peringatan dini berbasis Twitter.
- Membantu organisasi bantuan bencana dalam mengoptimalkan respon terhadap kejadian darurat.
- Menyelidiki dampak media sosial terhadap persepsi publik terhadap bencana.

### Import Libraries
"""

import nltk
from nltk.corpus import stopwords

import numpy as np
import pandas as pd
import time, datetime
import random, re

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler, random_split
from transformers import BertForSequenceClassification, AdamW, BertConfig, BertTokenizer, get_linear_schedule_with_warmup

"""<font color="red">**- - - - MOHON DIPERHATIKAN - - - -**</font>
<br>**Aktifkan GPU sekarang.** Di Google Colab, klik **Runtime > Change Runtime Type**, lalu pilih **T4 GPU**.

### User-defined Functions (UDFs)
"""

def clean_text(text):

    # replacing everything with space except (a-z, A-Z, ".", "?", "!", ",")
    text = text.lower()
    text = re.sub(r"[^a-zA-Z?.!,¿]+", " ", text)

    # removing URLs
    text = re.sub(r"http\S+", "",text)

    # removing HTML tags
    html = re.compile(r'<.*?>')
    text = html.sub(r'',text)

    # removing punctuations
    punctuations = '@#!?+&*[]-%.:/();$=><|{}^' + "'`" + '_'
    for p in punctuations:
        text = text.replace(p, '')

    # removing stopwrods
    nltk.download('stopwords')
    sw = stopwords.words('english')

    text = [word.lower() for word in text.split() if word.lower() not in sw]
    text = " ".join(text)

    # removing emoji
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    return text

def flat_accuracy(preds, labels):
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()
    return np.sum(pred_flat == labels_flat) / len(labels_flat)

def format_time(elapsed):
    elapsed_rounded = int(round((elapsed)))
    return str(datetime.timedelta(seconds=elapsed_rounded))

def tokenizer_encode(text):

    # Call the BERT tokenizer
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)

    # Get max_len
    max_len = 0
    for sent in tweets:
        input_ids = tokenizer.encode(sent, add_special_tokens=True)
        max_len = max(max_len, len(input_ids))

    input_ids = []
    attention_masks = []

    for tweet in text:
        # `encode_plus` will:
        #   (1) Tokenize the sentence.
        #   (2) Prepend the `[CLS]` token to the start.
        #   (3) Append the `[SEP]` token to the end.
        #   (4) Map tokens to their IDs.
        #   (5) Pad or truncate the sentence to `max_length`
        #   (6) Create attention masks for [PAD] tokens.
        encoded_dict = tokenizer.encode_plus(
                            tweet,                          # Sentence to encode.
                            add_special_tokens = True,      # Add '[CLS]' and '[SEP]'
                            max_length = max_len,           # Pad & truncate all sentences.
                            pad_to_max_length = True,
                            return_attention_mask = True,   # Construct attn. masks.
                            return_tensors = 'pt',          # Return pytorch tensors.
                       )

        # Add the encoded sentence to the list.
        input_ids.append(encoded_dict['input_ids'])

        # And its attention mask (simply differentiates padding from non-padding).
        attention_masks.append(encoded_dict['attention_mask'])

    return input_ids, attention_masks

"""### Seeding (for reproducible results)"""

seed_val = 42
random.seed(seed_val)
np.random.seed(seed_val)
torch.manual_seed(seed_val)
torch.cuda.manual_seed_all(seed_val)

"""### Device Setup"""

# TODO: Aktifkan GPU (CUDA) sebagai device untuk training
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

"""### Data Loading and Preprocessing"""

# TODO: Impor data training
df = pd.read_csv('/content/train.csv')

df.head()

# TODO: Preprocess data test
df['text'] = df['text'].apply(clean_text)

# TODO: Tentukan X (features/text) dan Y (labels)
tweets = df['text'].values
labels = df['target'].values

"""### BERT Tokenizer on Train Set"""

input_ids, attention_masks = tokenizer_encode(tweets)

# Convert the lists into tensors.
input_ids = torch.cat(input_ids, dim=0)
attention_masks = torch.cat(attention_masks, dim=0)
labels = torch.tensor(labels)

# Combine the training inputs into a TensorDataset.
dataset = TensorDataset(input_ids, attention_masks, labels)

"""### Preparation for Training"""

# TODO: Pecah dataset menjadi 80% training dan 20% validation
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

print('{:>5,} training samples'.format(train_size))
print('{:>5,} validation samples'.format(val_size))

# TODO: Tentukan nilai batch
batch_size = 128

# TODO: Lengkapi DataLoader untuk training/validation

train_dataloader = DataLoader(
    dataset = train_dataset,
    sampler = RandomSampler(train_dataset),
    batch_size = batch_size
)

validation_dataloader = DataLoader(
    dataset = val_dataset,
    sampler = SequentialSampler(val_dataset),
    batch_size = batch_size
)

"""### Load BERT Classifer Model"""

model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels = 2, # TODO: Tentukan jumlah label klasifikasi
    output_attentions = False,
    output_hidden_states = False,
)

model = model.to(device)

"""### Model Fine-tuning"""

epochs = 5 # TODO: Tentukan jumlah epoch
learning_rate = 2e-5 # TODO: Tentukan learning rate

total_steps = len(train_dataloader) * epochs

# Set optimizer.
optimizer = AdamW(model.parameters(), lr = learning_rate)

# Create the learning rate scheduler.
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps = 0, num_training_steps = total_steps)

training_stats = []
total_t0 = time.time()

for epoch_i in range(0, epochs):

    # ========================================
    #               Training
    # ========================================

    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    # Measure how long the training epoch takes.
    t0 = time.time()
    total_train_loss = 0
    model.train()

    for step, batch in enumerate(train_dataloader):
        # `batch` contains three pytorch tensors:
        #   [0]: input ids
        #   [1]: attention masks
        #   [2]: labels

        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)

        # FORWARD PASS
        optimizer.zero_grad()
        output = model(b_input_ids,
                         token_type_ids=None,
                         attention_mask=b_input_mask,
                         labels=b_labels)

        loss = output.loss
        total_train_loss += loss.item()

        # BACKWARD PASS
        loss.backward()

        # Clip the norm of the gradients to 1.0.
        # This is to help prevent the "exploding gradients" problem.
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        # Update parameters and take a step using the computed gradient.
        # The optimizer dictates the "update rule"--how the parameters are
        # modified based on their gradients, the learning rate, etc.
        optimizer.step()

        # Update the learning rate.
        scheduler.step()

    # Calculate the average loss over all of the batches.
    avg_train_loss = total_train_loss / len(train_dataloader)

    # Measure how long this epoch took.
    training_time = format_time(time.time() - t0)
    print("")
    print("  Average training loss: {0:.2f}".format(avg_train_loss))
    print("  Training epcoh took: {:}".format(training_time))

    # ========================================
    #               Validation
    # ========================================

    print("")
    print("Running Validation...")

    t0 = time.time()
    model.eval()

    total_eval_accuracy = 0
    best_eval_accuracy = 0
    total_eval_loss = 0
    nb_eval_steps = 0

    for batch in validation_dataloader:
        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)

        with torch.no_grad():
            output= model(b_input_ids,
                                   token_type_ids=None,
                                   attention_mask=b_input_mask,
                                   labels=b_labels)

        loss = output.loss
        total_eval_loss += loss.item()

        # Move logits and labels to CPU if we are using GPU
        logits = output.logits
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        # Calculate the accuracy for this batch of test sentences, and
        # accumulate it over all batches.
        total_eval_accuracy += flat_accuracy(logits, label_ids)

    avg_val_accuracy = total_eval_accuracy / len(validation_dataloader)
    print("  Accuracy: {0:.2f}".format(avg_val_accuracy))

    # Calculate the average loss over all of the batches.
    avg_val_loss = total_eval_loss / len(validation_dataloader)

    # Measure how long the validation run took.
    validation_time = format_time(time.time() - t0)
    if avg_val_accuracy > best_eval_accuracy:
        torch.save(model, 'bert_model')
        best_eval_accuracy = avg_val_accuracy

    training_stats.append(
        {
            'epoch': epoch_i + 1,
            'Training Loss': avg_train_loss,
            'Valid. Loss': avg_val_loss,
            'Valid. Accur.': avg_val_accuracy,
            'Training Time': training_time,
            'Validation Time': validation_time
        }
    )

print("")
print("Training complete!")
print("Total training took {:} (h:mm:ss)".format(format_time(time.time()-total_t0)))

"""### Validation ACCURACY should reach >= 80%"""

# TODO: Jika akurasi masih dibawah 80%, silakan lakukan penyesuaian hyperparameters

"""### Load the Best Model"""

model = torch.load('bert_model')

"""### Final Evaluation (using Test Data)"""

# TODO: Impor data test
df_test = pd.read_csv('/content/test.csv')

# TODO: Preprocess data test
df_test['text'] = df_test['text'].apply(clean_text)
test_tweets = df_test['text'].values

test_input_ids, test_attention_masks = tokenizer_encode(test_tweets)

# Convert the lists into Tensor.
test_input_ids = torch.cat(test_input_ids, dim=0)
test_attention_masks = torch.cat(test_attention_masks, dim=0)

# Combine the training inputs into a TensorDataset.
test_dataset = TensorDataset(test_input_ids, test_attention_masks)

# TODO: Lengkapi DataLoader untuk testing
test_dataloader = DataLoader(
    dataset = test_dataset,
    sampler = SequentialSampler(test_dataset),
    batch_size = batch_size
)

predictions = []
for batch in test_dataloader:
    b_input_ids = batch[0].to(device)
    b_input_mask = batch[1].to(device)

    with torch.no_grad():
        output= model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask)
        logits = output.logits
        logits = logits.detach().cpu().numpy()
        pred_flat = np.argmax(logits, axis=1).flatten()

        predictions.extend(list(pred_flat))

df_output = pd.DataFrame()
df_output['text'] = df_test['text']
df_output['predict'] = predictions
df_output

"""### Scoring
Total `#TODO` = 14
<br>Checklist:

- [x] Aktifkan GPU (CUDA) sebagai device untuk training
- [x] Impor data training
- [x] Preprocess data training
- [x] Tentukan X (features/text) dan Y (labels)
- [x] Pecah dataset menjadi 80% training dan 20% validation
- [x] Tentukan nilai batch
- [x] Lengkapi DataLoader untuk training/validation
- [x] Tentukan jumlah label klasifikasi
- [x] Tentukan jumlah epoch
- [x] Tentukan jumlah learning rate
- [x] Jika akurasi masih dibawah 80%, silakan lakukan penyesuaian hyperparameters
- [x] Impor data test
- [x] Preprocess data test
- [x] Lengkapi DataLoader untuk testing

### Additional readings
* N/A

### Copyright © 2024 Startup Campus, Indonesia
* Prepared by **Nicholas Dominic, M.Kom.** [(profile)](https://linkedin.com/in/nicholas-dominic)
* You may **NOT** use this file except there is written permission from PT. Kampus Merdeka Belajar (Startup Campus).
* Please address your questions to mentors.
"""