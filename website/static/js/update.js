
function showAndHide() {
    selects = document.querySelectorAll('select')
    for (const s of selects) {
        if (s.disabled) {
            s.style.visibility = 'hidden';
        } else {
            s.style.visibility = 'visible';
        }
    }
}

// show the abled options, and hide the disabled options
function showAndHideOptions() {
    all_options = document.getElementsByTagName("option");
    for (let i = 0; i < all_options.length; ++i) {
        this_option = all_options[i];
        if (this_option.disabled) {
            this_option.setAttribute('hidden', 'hidden');
        } else {
            this_option.removeAttribute('hidden');
        }
    }
}

function OnActionChange() {

    var x = document.getElementById("sel_action").value;
    var select1 = document.getElementById("sel_action_para1");
    var select2 = document.getElementById("sel_action_para2");

    if (action_option_dict[x] != undefined) {
        var len = action_option_dict[x].length;
        if (len == 0) {
            select1.options.length = 0;
            select2.options.length = 0;
            $('#sel_action_para1').attr('disabled', true);
            $('#sel_action_para2').attr('disabled', true);
            showAndHide();
        }
        if (len == 1) {
            select1.options.length = 0;
            select2.options.length = 0;
            object_len = action_option_dict[x][0].length;

            for (let i = 0; i < object_len; i++) {
                select1.options.add(new Option(action_option_dict[x][0][i][0], action_option_dict[x][0][i][1]));
            }
            $('#sel_action_para1').attr('disabled', false);
            $('#sel_action_para2').attr('disabled', true);
            showAndHide();
        }
        if (len == 2) {
            select1.options.length = 0;
            select2.options.length = 0;
            object_len = action_option_dict[x][0].length;
            for (let i = 0; i < object_len; i++) {
                select1.options.add(new Option(action_option_dict[x][0][i][0], action_option_dict[x][0][i][1]));
            }
            object_len = action_option_dict[x][1].length;
            for (let i = 0; i < object_len; i++) {
                select2.options.add(new Option(action_option_dict[x][1][i][0], action_option_dict[x][1][i][1]));
            }
            $('#sel_action_para1').attr('disabled', false);
            $('#sel_action_para2').attr('disabled', false);
            showAndHide();
        }
    }
}


function OnIntentUpdate() {
    // sel_other_high_intent1-[0, 1, 2, 3, 4]
    let com = document.getElementById("sel_your_high_intent-0");
    options = com.options;
    for (let i = 0; i < options.length; i++) {
        flag = false;
        for (let j = 0; j <= 4; ++j) {
            if (intent_option_dict[j] == undefined) {
                continue;
            }
            items = intent_option_dict[j];
            for (item of items) {
                if (item.startsWith(options[i].value)) {
                    flag = true;
                }
            }
        }
        // 对于可取值完全被删除的动作，无法选择
        if (!flag) {
            options[i].disabled = true;
        } else {
            options[i].disabled = false;
        }
    }
}

function OnIntent2Update() {
    let your_high_intent = document.getElementById("sel_your_high_intent-0");
    options = your_high_intent.options;
    // option_dict = intent_option_dict[agent[0]];
    option_dict = intent_option_dict;

    for (let i = 0; i < options.length; ++i) {
        option = options[i];
        for (k in option_dict) {
            for (item of option_dict[k]) {
                if (item.startsWith(option.value) || option.value == 'NA') {
                    option.disabled = false;
                } else {
                }
            }
        }
    }

    if (belief_agent_list.length > 0) {

        let other_high_intent = document.getElementById("sel_other_high_intent1-0");
        options = other_high_intent.options;
        agent = belief_agent_list[0];
        option_dict = other_intent_option_dict[agent[0]];

        for (let i = 0; i < options.length; ++i) {
            option = options[i];
            for (k in option_dict) {
                for (item of option_dict[k]) {
                    if (item.startsWith(option.value) || option.value == 'NA') {
                        option.disabled = false;
                    } else {
                    }
                }
            }
        }
    }
}

function OnIntentChange() {
    var select_item = document.getElementById("sel_your_high_intent-0")
    var x = document.getElementById("sel_your_high_intent-0").value;
    prefix = 'sel_your_high_intent';
    number = 0;

    para1 = document.getElementById(prefix + '-' + (number+1));
    para2 = document.getElementById(prefix + '-' + (number+2));
    para3 = document.getElementById(prefix + '-' + (number+3));
    para4 = document.getElementById(prefix + '-' + (number+4));

    para1.options.length = 0;
    para1.disabled = true;
    para2.options.length = 0;
    para2.disabled = true;
    para3.options.length = 0;
    para3.disabled = true;
    para4.options.length = 0;
    para4.disabled = true;

    current_prefix = '' + x + '-';
    const set = new Set();
    for (let i = 1; i <= 4; ++i) {
        if (intent_option_dict[i] == undefined) {
            continue;
        }
        items = intent_option_dict[i];
        for (item of items) {
            if (!item.startsWith(current_prefix)) {
                continue;
            }
            remaining = item.slice(current_prefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            }
            else {
                set.add(remaining.split('-')[0]);
            }
        }
    }
    if (set.size > 0) {
        para1.disabled = false;
        showAndHide();
        if (!((x =="Observe") || (x=="Greet") || (x=="RespondTo"))){
            para1.options.add(new Option('NA', 'NA'));
        }
        for (item of set) {
            if (item in intent_desc_dict) {
                para1.options.add(new Option(intent_desc_dict[item], item));
            } else {
                para1.options.add(new Option(item, item));
            }
        }
    }

    var selectedOption = select_item.value;
    // 显示选中的选项
    var selectedOptionElement = document.getElementById("selectedMyIntention")
    if ((selectedOption=='PutInto') || (selectedOption=='PutOnto'))
        {selectedOptionElement.textContent = " put";}
    else if (selectedOption == 'PlayWith')
        {selectedOptionElement.textContent = " play";}
    // else if (selectedOption == 'RespondTo')
    //     {selectedOptionElement.textContent = " respond to"}
    else if (selectedOption == "RequestHelp")
        {selectedOptionElement.textContent = " request help from"}
    else if (selectedOption == "Get")
        {selectedOptionElement.textContent = " get"}
    else if (selectedOption == "Give")
        {selectedOptionElement.textContent = " give"}
    else if (selectedOption == "NA")
        {selectedOptionElement.textContent = ""}
    else if (selectedOption == "Observe")
        {selectedOptionElement.textContent = " observe "+ para1.options[0].value}
    else if (selectedOption == "Greet")
        {selectedOptionElement.textContent = " greet "+para1.options[0].value}
    else if (selectedOption == "RespondTo")
        {selectedOptionElement.textContent = " respond to "+para1.options[0].value}
    else{
        selectedOptionElement.textContent = " "+ selectedOption.toLowerCase()
    }

}

function OnIntPara1Change() {
    if (event == undefined) {
        return;
    }
    prefix = event.target.id.split('-')[0];

    first = document.getElementById(event.target.id.split('-')[0] + '-' + 0);
    var x = event.target.value;
    var next = document.getElementById(event.target.id.split('-')[0] + '-' + 2);
    current_prefix = first.value + '-' + x + '-';

    next.options.length = 0;
    next.disabled = true;
    para3 = document.getElementById(prefix + '-' + 3);
    para4 = document.getElementById(prefix + '-' + 4);
    para3.options.length = 0;
    para3.disabled = true;
    para4.options.length = 0;
    para4.disabled = true;

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (intent_option_dict[i] == undefined) {
            continue;
        }
        items = intent_option_dict[i];
        for (item of items) {
            if (!item.startsWith(current_prefix)) {
                continue;
            }
            remaining = item.slice(current_prefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            }
            else {
                set.add(remaining.split('-')[0]);
            }
        }
    }
    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }

    var selected_item_para1 = document.getElementById("sel_your_high_intent-1");
    var para1_current = selected_item_para1.value

    function innerFunc(para1){
        var main_intent = document.getElementById("sel_your_high_intent-0").value;
        var selectedOption = main_intent;
        var selectedOptionElement = document.getElementById("selectedMyIntention")
        if (selectedOption=='PutInto') 
            {selectedOptionElement.textContent = " put " +para1+ " into";}
        else if (selectedOption=='PutOnto')
            {selectedOptionElement.textContent = " put " +para1+ " on";}
        else if (selectedOption == 'PlayWith')
            {selectedOptionElement.textContent = " play " + " " + para1;}
        else if (selectedOption == 'RespondTo')
            {selectedOptionElement.textContent = " respond to " + para1;}
        else if (selectedOption == "RequestHelp")
            {selectedOptionElement.textContent = " request help from " + para1}
        else if (selectedOption == "Get")
            {selectedOptionElement.textContent = " get "+para1}
        else if (selectedOption == "Give")
            {selectedOptionElement.textContent = " give " + para1}
        else{
            selectedOptionElement.textContent = " " + selectedOption.toLowerCase() + " " + para1
        }  
    }
  
    if (!(para1_current == "NA"))
        {innerFunc(para1_current)}
    else{
        innerFunc("")
    }


}

function OnIntPara2Change() {
    if (event == undefined) {
        return;
    }
    first = document.getElementById(event.target.id.split('-')[0] + '-' + 0);
    second = document.getElementById(event.target.id.split('-')[0] + '-' + 1);
    var x = event.target.value;
    var next = document.getElementById(event.target.id.split('-')[0] + '-' + 3);
    next.options.length = 0;
    current_prefix = first.value + '-' + second.value + '-' + x + '-';

    para4 = document.getElementById(prefix + '-' + 4);
    para4.options.length = 0;
    para4.disabled = true;

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (intent_option_dict[i] == undefined) {
            continue;
        }
        items = intent_option_dict[i];
        for (item of items) {
            if (!item.startsWith(current_prefix)) {
                continue;
            }
            remaining = item.slice(current_prefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            }
            else {
                set.add(remaining.split('-')[0]);
            }
        }
    }
    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }

    var selected_item_para2 = document.getElementById("sel_your_high_intent-2");
    var selected_item_para1 = document.getElementById("sel_your_high_intent-1");
    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value

    function innerFunc(para1, para2){
        var main_intent = document.getElementById("sel_your_high_intent-0").value;
        var selectedOption = main_intent;
        var selectedOptionElement = document.getElementById("selectedMyIntention")
        if (selectedOption=='PutInto') 
            {selectedOptionElement.textContent = " put " +para1+ " into "+para2;}
        else if (selectedOption=='PutOnto')
            {selectedOptionElement.textContent = " put " +para1+ " on "+para2;}
        else if (selectedOption == 'PlayWith')
            {selectedOptionElement.textContent = " play " + " " + para1 + " with " + para2;}
        else if (selectedOption == "RequestHelp")
            {
                var selectedOptionSub = para2
                var para2_sub
                if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                    {para2_sub = " put";}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play";}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to"}
                // else if (selectedOptionSub == "RequestHelp")
                    // {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get"}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give"}
                else{
                    para2_sub = " "+para2.toLowerCase()
                }
                selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;
    
            }
        else if (selectedOption == "Get")
            {selectedOptionElement.textContent = " get "+ para1 + " from "+para2}
        else if (selectedOption == "Give")
            {selectedOptionElement.textContent = " give " + para1 + " to " + para2}
        else if (selectedOption == "Help")
            { 
                var selectedOptionSub = para2
                var para2_sub
                if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                    {para2_sub = " put";}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play";}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to"}
                // else if (selectedOptionSub == "RequestHelp")
                    // {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get"}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give"}
                else{
                    para2_sub = " "+para2.toLowerCase()
                }
                selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
            }
        else if (selectedOption == "Harm")
            {
                var selectedOptionSub = para2
                var para2_sub
                if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                    {para2_sub = " put";}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play";}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to"}
                // else if (selectedOptionSub == "RequestHelp")
                    // {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get"}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give"}
                else{
                    para2_sub = " "+para2.toLowerCase()
                }
                selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
                }
        else{
                selectedOptionElement.textContent = " " + selectedOption.toLowerCase() + " " + para1 +" "+ para2
            }
        }
    
        if (!(para2_c=="NA")){
            innerFunc(para1_c,para2_c)
        }else{
            innerFunc(para1_c,"")
        }

}

function OnIntPara3Change() {
    if (event == undefined) {
        return;
    }
    first = document.getElementById(event.target.id.split('-')[0] + '-' + 0);
    second = document.getElementById(event.target.id.split('-')[0] + '-' + 1);
    third = document.getElementById(event.target.id.split('-')[0] + '-' + 2);
    var x = event.target.value;
    var next = document.getElementById(event.target.id.split('-')[0] + '-' + 4);
    next.options.length = 0;
    current_prefix = first.value + '-' + second.value + '-' + third.value + '-' + x + '-';

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (intent_option_dict[i] == undefined) {
            continue;
        }
        items = intent_option_dict[i];
        for (item of items) {
            if (!item.startsWith(current_prefix)) {
                continue;
            }
            remaining = item.slice(current_prefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            }
            else {
                set.add(remaining.split('-')[0]);
            }
        }
    }
    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }

    var selected_item_para3 = document.getElementById("sel_your_high_intent-3");
    var selected_item_para2 = document.getElementById("sel_your_high_intent-2");
    var selected_item_para1 = document.getElementById("sel_your_high_intent-1");
    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value
    var para3_c = selected_item_para3.value

    function innerFunc(para1,para2,para3){
        var selectedOptionElement = document.getElementById("selectedMyIntention")
        var main_intent = document.getElementById("sel_your_high_intent-0").value;
        var selectedOption = main_intent;
        if (selectedOption == "RequestHelp")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                // else if (selectedOptionSub == "RequestHelp")
                //     {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase()+ " "+para3
                }
                selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;

            }
        else if (selectedOption == "Help")
            { 
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase()+ " "+para3
                }
                selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
            }
        else if (selectedOption == "Harm")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                // else if (selectedOptionSub == "RequestHelp")
                //     {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase()+ " "+para3
                }
                selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
            }
    }

    if (!(para3_c=='NA')){
        innerFunc(para1_c,para2_c,para3_c)
    }else{
        innerFunc(para1_c,para2_c,"")
    }
    
}

function OnIntPara4Change(){
    var selected_item_para4 = document.getElementById("sel_your_high_intent-4");
    var selected_item_para3 = document.getElementById("sel_your_high_intent-3");
    var selected_item_para2 = document.getElementById("sel_your_high_intent-2");
    var selected_item_para1 = document.getElementById("sel_your_high_intent-1");

    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value
    var para3_c = selected_item_para3.value
    var para4_c = selected_item_para4.value
    

    function innerFunc(para1,para2,para3,para4){
        var main_intent = document.getElementById("sel_your_high_intent-0").value;
        var selectedOption = main_intent;
        var selectedOptionElement = document.getElementById("selectedMyIntention")
        if (selectedOption == "RequestHelp")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" on "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOption == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;

            }
        else if (selectedOption == "Help")
            { 
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" onto "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOptionSub == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
            }
        else if (selectedOption == "Harm")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" onto "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOptionSub == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
            }
    }

    if (!(para4_c=="NA")){
        innerFunc(para1_c,para2_c,para3_c,para4_c)
    }else{
        innerFunc(para1_c,para2_c,para3_c,"")
    }

    
}



function OnIntent2Change() {

    var select_item = document.getElementById("sel_other_high_intent1-0")
    var x = document.getElementById("sel_other_high_intent1-0").value;
    prefix = 'sel_other_high_intent1';
    number = 0;

    para1 = document.getElementById(prefix + '-' + (number+1));
    para2 = document.getElementById(prefix + '-' + (number+2));
    para3 = document.getElementById(prefix + '-' + (number+3));
    para4 = document.getElementById(prefix + '-' + (number+4));

    para1.options.length = 0;
    para1.disabled = true;
    para2.options.length = 0;
    para2.disabled = true;
    para3.options.length = 0;
    para3.disabled = true;
    para4.options.length = 0;
    para4.disabled = true;

    // option_dict = other_intent_option_dict[belief_agent_list[0][0]];

    if (!belief_agent_list || 
        !Array.isArray(belief_agent_list) || 
        belief_agent_list.length === 0 || 
        !belief_agent_list[0] || 
        !belief_agent_list[0][0] ||
        !other_intent_option_dict ||
        typeof other_intent_option_dict !== 'object' ||
        Object.keys(other_intent_option_dict).length === 0) {
        console.log("Required data structures are not properly defined");
        return;
    }

    const agent_key = belief_agent_list[0][0];
    const option_dict = other_intent_option_dict[agent_key];
    
    current_prefix = '' + x + '-';
    const set = new Set();
    for (let i = 1; i <= 4; ++i) {
        if (option_dict[i] == undefined) {
            continue;
        }
        items = option_dict[i];
        for (item of items) {
            if (!item.startsWith(current_prefix)) {
                continue;
            }
            remaining = item.slice(current_prefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            }
            else {
                set.add(remaining.split('-')[0]);
            }
        }
    }
    if (set.size > 0) {
        para1.disabled = false;
        showAndHide();
        if (!((x =="Observe") || (x=="Greet") || (x=="RespondTo"))){
            para1.options.add(new Option('NA', 'NA'));
        }
        for (item of set) {
            if (item in intent_desc_dict) {
                para1.options.add(new Option(intent_desc_dict[item], item));
            } else {
                para1.options.add(new Option(item, item));
            }
        }
    }


    var selectedOption = select_item.value;
    // 显示选中的选项
    var selectedOptionElement = document.getElementById("selectedOtherIntention")
    if ((selectedOption=='PutInto') || (selectedOption=='PutOnto'))
        {selectedOptionElement.textContent = " put";}
    else if (selectedOption == 'PlayWith')
        {selectedOptionElement.textContent = " play";}
    // else if (selectedOption == 'RespondTo')
    //     {selectedOptionElement.textContent = " respond to"}
    else if (selectedOption == "RequestHelp")
        {selectedOptionElement.textContent = " request help from"}
    else if (selectedOption == "Get")
        {selectedOptionElement.textContent = " get"}
    else if (selectedOption == "Give")
        {selectedOptionElement.textContent = " give"}
    else if (selectedOption == "NA")
        {selectedOptionElement.textContent = ""}
    else if (selectedOption == "Observe")
        {selectedOptionElement.textContent = " observe "+ para1.options[0].value}
    else if (selectedOption == "Greet")
        {selectedOptionElement.textContent = " greet "+para1.options[0].value}
    else if (selectedOption == "RespondTo")
        {selectedOptionElement.textContent = " respond to "+para1.options[0].value}
    else{
        selectedOptionElement.textContent = " "+ selectedOption.toLowerCase()
    }

    showAndHideOptions();
}

function OnInt2Para1Change() {

    const prefix = 'sel_other_high_intent1';
    const first = document.getElementById(`${prefix}-0`);
    const current = document.getElementById(`${prefix}-1`);
    const next = document.getElementById(`${prefix}-2`);
    const para3 = document.getElementById(`${prefix}-3`);
    const para4 = document.getElementById(`${prefix}-4`);

    if (!first || !current || !next) {
        console.log("Required elements not found");
        return;
    }

    const x = current.value;
    const currentPrefix = `${first.value}-${x}-`;

    next.options.length = 0;
    next.disabled = true;
    para3.options.length = 0;
    para3.disabled = true;
    para4.options.length = 0;
    para4.disabled = true;

    // const option_dict = other_intent_option_dict[belief_agent_list[0][0]];
    
    // Check if all required objects and properties exist
    if (!belief_agent_list || 
        !Array.isArray(belief_agent_list) || 
        belief_agent_list.length === 0 || 
        !belief_agent_list[0] || 
        !belief_agent_list[0][0] ||
        !other_intent_option_dict ||
        typeof other_intent_option_dict !== 'object' ||
        Object.keys(other_intent_option_dict).length === 0) {
        console.log("Required data structures are not properly defined");
        return;
    }

    const agent_key = belief_agent_list[0][0];
    const option_dict = other_intent_option_dict[agent_key];

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (option_dict[i] == undefined) {
            continue;
        }
        const items = option_dict[i];
        for (const item of items) {
            if (!item.startsWith(currentPrefix)) {
                continue;
            }
            const remaining = item.slice(currentPrefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            } else {
                set.add(remaining.split('-')[0]);
            }
        }
    }

    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (const item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }

    var selected_item_para1 = document.getElementById("sel_other_high_intent1-1");
    var para1_current = selected_item_para1.value
    // 显示选中的选项
    
    function innerFunc(para1){
        var main_intent = document.getElementById("sel_other_high_intent1-0").value;
        var selectedOption = main_intent;
        var selectedOptionElement = document.getElementById("selectedOtherIntention")
        if (selectedOption=='PutInto') 
            {selectedOptionElement.textContent = " put " +para1+ " into";}
        else if (selectedOption=='PutOnto')
            {selectedOptionElement.textContent = " put " +para1+ " on";}
        else if (selectedOption == 'PlayWith')
            {selectedOptionElement.textContent = " play " + " " + para1;}
        else if (selectedOption == 'RespondTo')
            {selectedOptionElement.textContent = " respond to " + para1;}
        else if (selectedOption == "RequestHelp")
            {selectedOptionElement.textContent = " request help from " + para1}
        else if (selectedOption == "Get")
            {selectedOptionElement.textContent = " get "+para1}
        else if (selectedOption == "Give")
            {selectedOptionElement.textContent = " give " + para1}
        else{
            selectedOptionElement.textContent = " " + selectedOption.toLowerCase() + " " + para1
        }  
    }
  
    if (!(para1_current == "NA"))
        {innerFunc(para1_current)}
    else{
        innerFunc("")
    }

}


function OnInt2Para2Change() {
    const prefix = 'sel_other_high_intent1';
    const first = document.getElementById(`${prefix}-0`);
    const second = document.getElementById(`${prefix}-1`);
    const current = document.getElementById(`${prefix}-2`);
    const next = document.getElementById(`${prefix}-3`);
    const para4 = document.getElementById(`${prefix}-4`);

    if (!first || !second || !current || !next) {
        console.log("Required elements not found");
        return;
    }

    const x = current.value;
    const currentPrefix = `${first.value}-${second.value}-${x}-`;

    next.options.length = 0;
    next.disabled = true;
    para4.options.length = 0;
    para4.disabled = true;

    if (!belief_agent_list || 
        !Array.isArray(belief_agent_list) || 
        belief_agent_list.length === 0 || 
        !belief_agent_list[0] || 
        !belief_agent_list[0][0] ||
        !other_intent_option_dict ||
        typeof other_intent_option_dict !== 'object' ||
        Object.keys(other_intent_option_dict).length === 0) {
        console.log("Required data structures are not properly defined");
        return;
    }

    const agent_key = belief_agent_list[0][0];
    const option_dict = other_intent_option_dict[agent_key];

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (option_dict[i] == undefined) {
            continue;
        }
        const items = option_dict[i];
        for (const item of items) {
            if (!item.startsWith(currentPrefix)) {
                continue;
            }
            const remaining = item.slice(currentPrefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            } else {
                set.add(remaining.split('-')[0]);
            }
        }
    }

    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (const item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }

    var selected_item_para2 = document.getElementById("sel_other_high_intent1-2");
    var selected_item_para1 = document.getElementById("sel_other_high_intent1-1");
    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value
    
    function innerFunc(para1, para2){
    var main_intent = document.getElementById("sel_other_high_intent1-0").value;
    var selectedOption = main_intent;
    var selectedOptionElement = document.getElementById("selectedOtherIntention")
    if (selectedOption=='PutInto') 
        {selectedOptionElement.textContent = " put " +para1+ " into "+para2;}
    else if (selectedOption=='PutOnto')
        {selectedOptionElement.textContent = " put " +para1+ " on "+para2;}
    else if (selectedOption == 'PlayWith')
        {selectedOptionElement.textContent = " play " + " " + para1 + " with " + para2;}
    else if (selectedOption == "RequestHelp")
        {
            var selectedOptionSub = para2
            var para2_sub
            if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                {para2_sub = " put";}
            else if (selectedOptionSub == 'PlayWith')
                {para2_sub = " play";}
            else if (selectedOptionSub == 'RespondTo')
                {para2_sub = " respond to"}
            // else if (selectedOptionSub == "RequestHelp")
                // {para2_sub = " request help from"}
            else if (selectedOptionSub == "Get")
                {para2_sub = " get"}
            else if (selectedOptionSub == "Give")
                {para2_sub = " give"}
            else{
                para2_sub = " "+para2.toLowerCase()
            }
            selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;

        }
    else if (selectedOption == "Get")
        {selectedOptionElement.textContent = " get "+ para1 + " from "+para2}
    else if (selectedOption == "Give")
        {selectedOptionElement.textContent = " give " + para1 + " to " + para2}
    else if (selectedOption == "Help")
        { 
            var selectedOptionSub = para2
            var para2_sub
            if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                {para2_sub = " put";}
            else if (selectedOptionSub == 'PlayWith')
                {para2_sub = " play";}
            else if (selectedOptionSub == 'RespondTo')
                {para2_sub = " respond to"}
            // else if (selectedOptionSub == "RequestHelp")
                // {para2_sub = " request help from"}
            else if (selectedOptionSub == "Get")
                {para2_sub = " get"}
            else if (selectedOptionSub == "Give")
                {para2_sub = " give"}
            else{
                para2_sub = " "+para2.toLowerCase()
            }
            selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
        }
    else if (selectedOption == "Harm")
        {
            var selectedOptionSub = para2
            var para2_sub
            if ((selectedOptionSub=='PutInto') || (selectedOptionSub=='PutOnto'))
                {para2_sub = " put";}
            else if (selectedOptionSub == 'PlayWith')
                {para2_sub = " play";}
            else if (selectedOptionSub == 'RespondTo')
                {para2_sub = " respond to"}
            // else if (selectedOptionSub == "RequestHelp")
                // {para2_sub = " request help from"}
            else if (selectedOptionSub == "Get")
                {para2_sub = " get"}
            else if (selectedOptionSub == "Give")
                {para2_sub = " give"}
            else{
                para2_sub = " "+para2.toLowerCase()
            }
            selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
            }
    else{
            selectedOptionElement.textContent = " " + selectedOption.toLowerCase() + " " + para1 +" "+ para2
        }
    }

    if (!(para2_c=="NA")){
        innerFunc(para1_c,para2_c)
    }else{
        innerFunc(para1_c,"")
    }
}

function OnInt2Para3Change() {
    const prefix = 'sel_other_high_intent1';
    const first = document.getElementById(`${prefix}-0`);
    const second = document.getElementById(`${prefix}-1`);
    const third = document.getElementById(`${prefix}-2`);
    const current = document.getElementById(`${prefix}-3`);
    const next = document.getElementById(`${prefix}-4`);

    if (!first || !second || !third || !current || !next) {
        console.log("Required elements not found");
        return;
    }

    const x = current.value;
    const currentPrefix = `${first.value}-${second.value}-${third.value}-${x}-`;

    next.options.length = 0;
    next.disabled = true;

    // const option_dict = other_intent_option_dict[belief_agent_list[0][0]];

    if (!belief_agent_list || 
        !Array.isArray(belief_agent_list) || 
        belief_agent_list.length === 0 || 
        !belief_agent_list[0] || 
        !belief_agent_list[0][0] ||
        !other_intent_option_dict ||
        typeof other_intent_option_dict !== 'object' ||
        Object.keys(other_intent_option_dict).length === 0) {
        console.log("Required data structures are not properly defined");
        return;
    }

    const agent_key = belief_agent_list[0][0];
    const option_dict = other_intent_option_dict[agent_key];

    const set = new Set();
    for (let i = 2; i <= 4; ++i) {
        if (option_dict[i] == undefined) {
            continue;
        }
        const items = option_dict[i];
        for (const item of items) {
            if (!item.startsWith(currentPrefix)) {
                continue;
            }
            const remaining = item.slice(currentPrefix.length);
            if (!remaining.includes('-')) {
                set.add(remaining);
            } else {
                set.add(remaining.split('-')[0]);
            }
        }
    }

    if (set.size > 0) {
        next.disabled = false;
        showAndHide();
        next.options.add(new Option('NA', 'NA'));
        for (const item of set) {
            if (item in intent_desc_dict) {
                next.options.add(new Option(intent_desc_dict[item], item));
            } else {
                next.options.add(new Option(item, item));
            }
        }
    }


    var selected_item_para3 = document.getElementById("sel_other_high_intent1-3"); 
    var selected_item_para2 = document.getElementById("sel_other_high_intent1-2");
    var selected_item_para1 = document.getElementById("sel_other_high_intent1-1");

    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value
    var para3_c = selected_item_para3.value
    
    
    function innerFunc(para1,para2,para3){
        var selectedOptionElement = document.getElementById("selectedOtherIntention")
        var main_intent = document.getElementById("sel_other_high_intent1-0").value;
        var selectedOption = main_intent;
        if (selectedOption == "RequestHelp")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                // else if (selectedOptionSub == "RequestHelp")
                //     {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase() + " "+para3
                }
                selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;

            }
        else if (selectedOption == "Help")
            { 
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase()+ " "+para3
                }
                selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
            }
        else if (selectedOption == "Harm")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put " + para3 + " into";}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put " + para3 + " on"}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+ para3;}
                else if (selectedOptionSub == 'RespondTo')
                    {para2_sub = " respond to " + para3}
                // else if (selectedOptionSub == "RequestHelp")
                //     {para2_sub = " request help from"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+ para3}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+ para3}
                else if (selectedOptionSub == "Inform")
                    {para2_sub = " inform " + para3}
                else if (selectedOptionSub == "Refer")
                    {para2_sub = " refer " + para3}
                else{
                    para2_sub = " "+para2.toLowerCase()+ " "+para3
                }
                selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
            }
    }

    if (!(para3_c=='NA')){
        innerFunc(para1_c,para2_c,para3_c)
    }else{
        innerFunc(para1_c,para2_c,"")
    }
    }

function OnInt2Para4Change(){
    var selected_item_para4 = document.getElementById("sel_other_high_intent1-4");
    var selected_item_para3 = document.getElementById("sel_other_high_intent1-3");
    var selected_item_para2 = document.getElementById("sel_other_high_intent1-2");
    var selected_item_para1 = document.getElementById("sel_other_high_intent1-1");
    
    var para1_c = selected_item_para1.value
    var para2_c = selected_item_para2.value
    var para3_c = selected_item_para3.value
    var para4_c = selected_item_para4.value
    

    function innerFunc(para1,para2,para3,para4){
        var main_intent = document.getElementById("sel_other_high_intent1-0").value;
        var selectedOption = main_intent;
        var selectedOptionElement = document.getElementById("selectedOtherIntention")
        if (selectedOption == "RequestHelp")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" on "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOption == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " request help from " + para1 + " to " + para2_sub;

            }
        else if (selectedOption == "Help")
            { 
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" onto "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOptionSub == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " help " + para1 + " to " + para2_sub;
            }
        else if (selectedOption == "Harm")
            {
                var selectedOptionSub = para2
                var para2_sub
                if (selectedOptionSub=='PutInto')
                    {para2_sub = " put "+para3+" into "+para4;}
                else if (selectedOptionSub=='PutOnto')
                    {para2_sub = " put "+para3+" onto "+para4;}
                else if (selectedOptionSub == 'PlayWith')
                    {para2_sub = " play "+para3+" with "+para4;}
                // else if (selectedOptionSub == 'RespondTo')
                //     {para2_sub = " respond to"}
                else if (selectedOptionSub == "Get")
                    {para2_sub = " get "+para3+" from "+para4;}
                else if (selectedOptionSub == "Give")
                    {para2_sub = " give "+para3+" to "+para4;}
                else{
                    // inform sb sth
                    para2_sub = " "+para2.toLowerCase()+" "+para3+" "+para4
                }
                selectedOptionElement.textContent = " harm " + para1 + " to " + para2_sub;
            }
    }

    if (!(para4_c=="NA")){
        innerFunc(para1_c,para2_c,para3_c,para4_c)
    }else{
        innerFunc(para1_c,para2_c,para3_c,"")
    }
}

function GetIntentKey() {
    intent_key = '';
    para1 = document.getElementById('sel_your_high_intent-0');
    para2 = document.getElementById('sel_your_high_intent-1');
    para3 = document.getElementById('sel_your_high_intent-2');
    para4 = document.getElementById('sel_your_high_intent-3');
    para5 = document.getElementById('sel_your_high_intent-4');
    if (!para1.disabled) {
        intent_key += para1.value;
    }
    if (!para2.disabled) {
        intent_key += '-' + para2.value;
    }
    if (!para3.disabled) {
        intent_key +=  '-' + para3.value;
    }
    if (!para4.disabled) {
        intent_key += '-' + para4.value;
    }
    if (!para5.disabled) {
        if (para5.value != '--') {
            intent_key += '-' + para5.value;
        }
    }
    // console.log(intent_key);
    return intent_key;
}

function GetOtherIntentKey() {
    intent_key = '';
    para1 = document.getElementById('sel_other_high_intent1-0');
    para2 = document.getElementById('sel_other_high_intent1-1');
    para3 = document.getElementById('sel_other_high_intent1-2');
    para4 = document.getElementById('sel_other_high_intent1-3');
    para5 = document.getElementById('sel_other_high_intent1-4');
    if (!para1.disabled) {
        intent_key += para1.value;
    }
    if (!para2.disabled) {
        intent_key += '-' + para2.value;
    }
    if (!para3.disabled) {
        intent_key +=  '-' + para3.value;
    }
    if (!para4.disabled) {
        intent_key += '-' + para4.value;
    }
    if (!para5.disabled) {
        if (para5.value != '--') {
            intent_key += '-' + para5.value;
        }
    }
    // console.log(intent_key);
    return intent_key;
}

function updateActionOptions(action_option_dict, action_name_array) {
    select = document.getElementById("sel_action");
    const prevValue1 = select.value;
    para1 = document.getElementById("sel_action_para1");
    const prevValue2 = para1.value;
    para2 = document.getElementById("sel_action_para2");
    const prevValue3 = para2.value;

    select.options.length = 0;
    keys = Object.keys(action_option_dict)

    for (let i = 0; i < action_name_array.length; ++i) {
        this_action = action_name_array[i];
        if (keys.includes(this_action)) {
            // new Option(text, value)
            select.options.add(new Option(action_name_dict[this_action], this_action));
        }
    }

    const index1 = Array.from(select.options).findIndex(option => option.value === prevValue1);
    const index2 = Array.from(para1.options).findIndex(option => option.value === prevValue2);
    const index3 = Array.from(para2.options).findIndex(option => option.value === prevValue3);

    if (index1 >= 0) {
        select.selectedIndex = index1;
        if (index2 >= 0) {
            para1.selectedIndex = index2;
            if (index3 >= 0) {
                para2.selectedIndex = index3;
            } else {
                OnActionChange();
            }
        } else {
            // -1
            OnActionChange();

            // 获取 .selector1 的元素
            var element = $(".selector1");

            // 检查元素是否存在
            if (element.length > 0) {
                // 检查 action_option_dict 和 select.value 的相关性
                if (action_option_dict.hasOwnProperty(select.value) &&
                    Array.isArray(action_option_dict[select.value]) && action_option_dict[select.value].length > 0 &&
                    Array.isArray(action_option_dict[select.value][0]) && action_option_dict[select.value][0].length > 0 &&
                    Array.isArray(action_option_dict[select.value][0][0]) && action_option_dict[select.value][0][0].length > 1) {
                    // 设置 .selector1 的值
                    element.val(action_option_dict[select.value][0][0][1]);
                }
            }
        }
    } else {
        OnActionChange();
    }
}