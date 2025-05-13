for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/action/action_analysis.py \
    --file_path ./experiment_res/llms_res/action_update_agent_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/action/${model} \
done

for model in Claude DeepSeek-R1 Gemini gpt-4o Llama3 Qwen3-8B Random
do
    python experiment_codes/llms/analysis/action/action_analysis.py \
    --file_path ./experiment_res/llms_res/action_update_agent_view_Model_${model}_for_testV1.csv \
    --output_dir ./experiment_codes/llms/analysis/action/${model}_top_3 \
    --top_3
done

python experiment_codes/llms/analysis/action/action_analysis.py \
    --file_path ./data/dataset_action_update_agent_view_segment_True_for_test.csv \
    --output_dir ./experiment_codes/llms/analysis/action/test \