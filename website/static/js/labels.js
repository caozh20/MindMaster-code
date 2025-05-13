
function state_bar_management() {
    var start_time = new Date().getTime();
    promise();
}

function promise() {
    var bar = document.getElementById('current-status');
    bar.innerHTML = 'Executing the actions in the environment.';
    setTimeout(function () {
        if (mode == "u2m") {
            waitting_interact();
        }
    }, wait_time);
}

function waitting_interact() {
    var bar = document.getElementById('current-status');
    bar.innerHTML = 'Waiting for the other player\'s action.';
}

// 展示标注框；（即标注别人的意图，标注自己的意图，标注下一步的 action）
function ShowLabelingBox() {
    var b = false;

    if (belief_agent_list.length > 0) {
        name = belief_agent_list[0][1];
        b = true;
    }

    label1 = document.getElementById("2.1");
    label2 = document.getElementById("2.2");
    label3 = document.getElementById("2.3");

    if (b) {
        ShowBeliefAgentLabel();
        label1.style.display = 'flex';
        label2.style.display = 'none';
        label3.style.display = 'none';
    } else {
        label1.style.display = 'none';
        label2.style.display = 'flex';
        label3.style.display = 'none';
    }
}

function ShowBeliefAgentLabel() {
    // 1. my estimation of other agent's intention
    // 2. options of estimation
    // 3. my estimation of other agent's value
    // 4. three value labels
    if (belief_agent_list.length > 0) {
        document.getElementById("2.1").style.display = "inline";
        // 暂时只显示一个 other agent
        // for (let i = 0; i < belief_agent_list.length; i++) {
        for (let i = 0; i < 1; i++) {
            document.getElementById("2.1."+(i+1)).style.display = "inline";
            agent = belief_agent_list[i];
            document.getElementById("name"+(i+1)+"1").innerHTML = "My estimation of " + "<b><span style='color: #50ABF1;'>" + agent[1] + "'s" + "</span></b>" + " intention:";
            document.getElementById("name"+(i+1)+"2").innerHTML = "My estimation of " + "<b><span style='color: #50ABF1;'>" + agent[1] + "'s" + "</span></b>" + " value:";
        }
    }
}

function Label1Done() {
    // 获取对应的文本框内容
    const explanationText = document.getElementById("explanation1").value.trim();
    
    // 检查文本框是否为空
    if (explanationText === "") {
        alert("请输入解释！");
        return;  // 终止函数执行，不进行后续操作
    }

    if (gb_survey_flag) {
        // 获取对应的文本框内容
        const explanationText = document.getElementById("explanation3").value.trim();
            
        // 检查文本框是否为空
        if (explanationText === "") {
            alert("请输入解释！");
            return;  // 终止函数执行，不进行后续操作
        }

        // immediately disable the button and waiting for the response
        $('#run').attr("disabled", true);

        // your_high_intent
        // other_high_intent
        your_high_intent = '';
        other_high_intent = '';

        if (belief_agent_list.length > 0) {
            belief_agent_id = belief_agent_list[0][0];
            other_high_intent = belief_agent_id + "|";
        }

        for (let i = 0; i < 5; ++i){
            val = $('#sel_your_high_intent-' + i).val();
            if (val != null) {
                value = world_id_name_dict[val];
                if (value == undefined) {
                    value = val;
                }
                your_high_intent += value + '-';
            }
            val = $('#sel_other_high_intent1-' + i).val();
            if (val != null) {
                value = world_id_name_dict[val];
                if (value == undefined) {
                    value = val;
                }
                other_high_intent += value + '-';
            }
        }

        if (other_high_intent.endsWith('-')) {
            other_high_intent = other_high_intent.slice(0, other_high_intent.length-1);
        }
        $.ajax({
            url: '/' + mode + '/survey',
            type: 'POST',
            dataType: 'json',
            data: {
                'other_desire': $('#sel_other_desire_active').val() + ',' + $('#sel_other_desire_social').val() + ',' + $('#sel_other_desire_helpful').val() ,
                'other_high_intent': other_high_intent,
                'explanation1': explanationText, 
            },
            async: false,
            success: function(recv) {
                gb_thanks_flag = true
            }
        });
    } else {
        label1 = document.getElementById("2.1");
        label2 = document.getElementById("2.2");
        label3 = document.getElementById("2.3");
        label1.style.display = 'none';
        label2.style.display = 'flex';
        label3.style.display = 'none';
    }
}

function Label2Done() {
    // 获取对应的文本框内容
    const explanationText = document.getElementById("explanation2").value.trim();
    
    // 检查文本框是否为空
    if (explanationText === "") {
        alert("请输入解释！");
        return;  // 终止函数执行，不进行后续操作
    }

    label1 = document.getElementById("2.1");
    label2 = document.getElementById("2.2");
    label3 = document.getElementById("2.3");
    label1.style.display = 'none';
    label2.style.display = 'none';
    label3.style.display = 'flex';
}

function Label3Done() {
    label1 = document.getElementById("2.1");
    label2 = document.getElementById("2.2");
    label3 = document.getElementById("2.3");
    label1.style.display = 'none';
    label2.style.display = 'none';
    label3.style.display = 'none';
}

function CloseBeliefAgentLabel() {
    Label3Done();
}


function ResetActionOptions(action_option_dict, action_name_dict) {
    // action init
    select = document.getElementById("sel_action");
    select.options.length = 0;
    // Add the blank default option
    select.options.add(new Option("Select an action", "", true, true));
    console.log('select an action added!!!')
    select.options[0].disabled = true;
    select.options[0].hidden = true;

    keys = Object.keys(action_option_dict)
    for (let i = 0; i < action_name_array.length; ++i) {
        this_action = action_name_array[i];
        if (keys.includes(this_action)) {
            // new Option(text, value)
//            console.log(this_action, action_name_dict[this_action]);
            select.options.add(new Option(action_name_dict[this_action], this_action));
        }
    }
    // explore
//    select.selectedIndex = 0;
}


function autoSaveActionOptions(sel_action, sel_action_para1, sel_action_para2, action_option_dict, action_name_dict) {
    select = document.getElementById("sel_action");
//    console.log('auto save last action', sel_action, sel_action_para1, sel_action_para2);

    let hit = false;
    for (let i = 0; i < select.options.length; ++i) {
        this_option = select.options[i];
        if (this_option.value == sel_action) {
            this_option.selected = true;
            hit = true;
            OnActionChange();
            if (sel_action_para1 != null) {
                $(".selector1").val(sel_action_para1);
                if (sel_action_para2 != null) {
                    $(".selector2").val(sel_action_para2);
                }
           } else {
                // the first option
                // 获取 .selector1 的元素
                var element = $(".selector1");

                // 检查元素是否存在
                if (element.length > 0) {
                    // 检查 action_option_dict 和 this_option.value 的相关性
                    if (action_option_dict.hasOwnProperty(this_option.value) &&
                        Array.isArray(action_option_dict[this_option.value]) && action_option_dict[this_option.value].length > 0 &&
                        Array.isArray(action_option_dict[this_option.value][0]) && action_option_dict[this_option.value][0].length > 0 &&
                        Array.isArray(action_option_dict[this_option.value][0][0]) && action_option_dict[this_option.value][0][0].length > 1) {

                        // 设置 .selector1 的值
                        element.val(action_option_dict[this_option.value][0][0][1]);
                    }
                }
           }
        }
    }

    if (hit == false) {
        ResetActionOptions(action_option_dict, action_name_dict);
        $('#sel_action_para1').attr('disabled', true);
        $('#sel_action_para2').attr('disabled', true);
        showAndHide();
    }
}
