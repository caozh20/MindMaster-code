for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/value/value_analysis.py \
    --data_path ./experiment_res/llms_res/value_pred_agent_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/value/${model}_agent_view
done

python experiment_codes/llms/analysis/value/value_analysis.py \
    --data_path ./data/dataset_value_pred_agent_view_segment_True_for_test.csv \
    --output_dir ./experiment_codes/llms/analysis/value/test_agent_view \
    --test

for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/value/value_analysis.py \
    --data_path ./experiment_res/llms_res/value_pred_world_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/value/${model}_world_view
done

python experiment_codes/llms/analysis/value/value_analysis.py \
    --data_path ./data/dataset_value_pred_world_view_segment_True_for_test.csv \
    --output_dir ./experiment_codes/llms/analysis/value/test_world_view \
    --test