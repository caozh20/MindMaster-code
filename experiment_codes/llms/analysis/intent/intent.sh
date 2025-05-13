for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./experiment_res/llms_res/intent_pred_agent_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/${model}_agent_view \
    --intent_column most_possible_intention \
    --analyze_type intent
done

for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./experiment_res/llms_res/intent_pred_agent_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/${model}_agent_view_top_3 \
    --intent_column most_possible_intention \
    --analyze_type intent \
    --top_3
done

python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./data/dataset_intent_pred_agent_view_segment_True_for_test.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/test_agent_view \
    --analyze_type intent

for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./experiment_res/llms_res/intent_pred_world_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/${model}_world_view \
    --intent_column most_possible_intention \
    --analyze_type intent
done

for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./experiment_res/llms_res/intent_pred_world_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/${model}_world_view_top_3 \
    --intent_column most_possible_intention \
    --analyze_type intent \
    --top_3
done

python experiment_codes/llms/analysis/intent/main_data_analyze.py \
    --intent_path ./data/dataset_intent_pred_world_view_segment_True_for_test.csv \
    --output_dir ./experiment_codes/llms/analysis/intent/test_world_view \
    --analyze_type intent