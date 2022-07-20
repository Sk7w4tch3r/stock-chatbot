import argparse
import re
from collections import Counter

from datasets import load_metric
from transformers import AutoModelForQuestionAnswering, AutoTokenizer

from read_ds import c2dict, read_qa
from utils import AnswerPredictor


def cleaner(text):
    return re.sub('\u200c', " ", text).strip()
  
# -------------------------------------------------------------------- Method One (datasets.load_metric)
def compute_HF_squad_metrics(preds, answers):
    
    metric = load_metric("squad_v2")

    formatted_preds = [{"id": str(k), 
                        "prediction_text": cleaner(v['text']),
                        "no_answer_probability": 0.0} 
                        for k, v in preds.items()]

    references = [{"id": str(i), 
                "answers": {'answer_start': a['answer_start'], 
                            'text': map(cleaner, a['text'])}}
                for i, a in enumerate(answers)]

    return metric.compute(predictions=formatted_preds, references=references)

# ------------------------------------------------------------------- Method Two (offical SQuADv2)
# offical SQuAD2.0 evaluation script. Modifed slightly for this dataset
def f1_score(prediction, ground_truth):
    prediction_tokens = cleaner(prediction)
    ground_truth_tokens = cleaner(ground_truth)
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def exact_match_score(prediction, ground_truth):
    return (cleaner(prediction) == cleaner(ground_truth))


def metric_max_over_ground_truths(metric_fn, prediction, ground_truths):
    scores_for_ground_truths = []
    for ground_truth in ground_truths:
        score = metric_fn(prediction, ground_truth)
        scores_for_ground_truths.append(score)
    
    return max(scores_for_ground_truths)


def evaluate(gold_answers, predictions):
    f1 = exact_match = total = 0
    for ground_truths, prediction in zip(gold_answers, predictions):
        total += 1
        exact_match += metric_max_over_ground_truths(exact_match_score, prediction, ground_truths)
        f1 += metric_max_over_ground_truths(f1_score, prediction, ground_truths)
    exact_match = 100.0 * exact_match / total
    f1 = 100.0 * f1 / total
    return {'exact_match': exact_match, 'f1': f1}

def official_squad_metrics(preds, answers):
      
    y_hat = [v['text'] for v in preds.values()]
    y = [v['text'] if len(v['text'])>0 else [''] for v in answers]

    return evaluate(y, y_hat)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, default=r'..\service\models\albert-fa-base-v2-finetuned-persian_qa')
    parser.add_argument('--test_ds', type=str, default=r'..\..\dataset\Stock-QA.json')
    args = parser.parse_args()
    model_name = args.model_name
    test_ds = args.test_ds

    model = AutoModelForQuestionAnswering.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # loading testset
    test_ds = c2dict(read_qa('..\..\dataset\Stock-QA.json'))
    questions, contexts, answers = test_ds['question'], test_ds['context'], test_ds['answers']

    # creating predictions
    predictor = AnswerPredictor(model, tokenizer)
    preds = predictor(questions, contexts, batch_size=1)
    print(preds[0])

    # computing official SQuAD metrics
    print(official_squad_metrics(preds, answers))

    # computing HuggingFace SQuAD2.0 metrics
    print(compute_HF_squad_metrics(preds, answers))
