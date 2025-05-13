document.addEventListener("DOMContentLoaded", function() {
    const gifs = [
        { name: "Eat", url: "gif/eat.gif", description: "['Eat', 'banana_3']: Eat banana_3." },
        { name: "FollowPointing", url: "gif/follow_pointing.gif", description: "['FollowPointing', 'agent 2']: Follow agent 2's pointing to banana_3." },
        { name: "Give..To..", url: "gif/give_to.gif", description: "['Give..To..', 'key_3', 'agent 2']: Give key_3 to agent 2." },
        { name: "Grab", url: "gif/grab.gif", description: "['Grab', 'dumbbell_3']: Grab dumbbell_3." },
        { name: "MoveTo", url: "gif/move_to.gif", description: "['MoveTo', 'cup_3']: Move to cup_3." },
        { name: "MoveToAttention", url: "gif/move_to_attention.gif", description: "['MoveToAttention', 'agent 2']: Move to agent 2's attention field." },
        { name: "NodHead", url: "gif/nod_head.gif", description: "['NodHead']: Nod head." },
        { name: "Open", url: "gif/open.gif", description: "['Open', 'box_3']: Open box_3." },
        { name: "PointTo", url: "gif/point_to.gif", description: "['PointTo', 'shelf_3']: Point to shelf_3." },
        { name: "Put..Into..", url: "gif/put_into.gif", description: "['Put..Into..', 'banana_3', 'shelf_4']: Put banana_3 into shelf_4." },
        { name: "Put..Onto..", url: "gif/put_onto.gif", description: "['Put..Onto..', 'dumbbell_3', 'table_4']: Put dumbbell_3 onto table_4." },
        { name: "Put..Down", url: "gif/put_down.gif", description: "['Put..Down', 'banana_3']: Put down banana_3." },
        { name: "RotateTo", url: "gif/rotate_to.gif", description: "['RotateTo', 'banana_3']: Rotate to banana_3." },
        { name: "ShakeHead", url: "gif/shake_head.gif", description: "['ShakeHead']: Shake head." },
        { name: "Smash", url: "gif/smash.gif", description: "['Smash', 'cup_3']: Smash cup_3." },
        { name: "Speak", url: "gif/speak.gif", description: "['Speak', 'Hello']: Speak the word 'Hello'." },
        { name: "Unlock", url: "gif/unlock.gif", description: "['Unlock', 'box_4', 'key_3']: Unlock box_4 with key_3." },
        { name: "WaveHand", url: "gif/wave_hand.gif", description: "['WaveHand']: Wave hand." },
        { name: "PerformEat", url: "gif/perform_eat.gif", description: "['Perform', 'Eat']: Perform eating." },
        { name: "PerformDrink", url: "gif/perform_drink.gif", description: "['Perform', 'Drink']: Perform drinking." }, 
        { name: "Play", url: "gif/play.gif", description: "['Play', 'chess_3', 'agent_2']: Play chess_3 with agent_2. "}, 
        { name: "Close", url: "gif/close.gif", description: "['Close', 'shelf_3']: Close shelf_3. "}
        // Add more GIFs as needed
      ];

    const intents = [
        { name: "Observe", url: "None", description: "['Observe', 'sb/sth']: Collect information about someone or something by observing." },
        { name: "Give..To..", url: "None", description: "['Give..To..', 'sth', 'sb']: Give something to someone." },
        { name: "Get..From..", url: "None", description: "['Get..From..', 'sth', 'sw/sb']: Obtain something from somewhere/somebody." },
        { name: "Find", url: "None", description: "['Find', 'sb/sth']: Locate someone or something." },
        { name: "Open", url: "None", description: "['Open', 'sth']: Open something." },
        { name: "Put..Into..", url: "None", description: "['Put..Into..', 'sth_1', 'sth_2']: Place something_1 into something_2." },
        { name: "Put..Onto..", url: "None", description: "['Put..Onto..', 'sth_1', 'sth_2']: Place something_1 onto something_2." },
        { name: "Play..With..", url: "None", description: "['Play..With..', 'sth', 'sb']: Play something with someone." },
        { name: "RespondTo", url: "None", description: "['RespondTo', 'sb']: Respond to someone's signal." },
        { name: "Inform", url: "None", description: "['Inform', 'sb', 'sth']: Let someone know something." },
        { name: "Greet", url: "None", description: "['Greet', 'sb']: Send a social signal to someone." },
        { name: "Help", url: "None", description: "['Help', 'sb', 'intent']: Assist someone with an intent." },
        { name: "RequestHelp", url: "None", description: "['RequestHelp', 'sb', 'intent']: Request someone's help to complete an intent." },
        { name: "Harm", url: "None", description: "['Harm', 'sb', 'intent']: Prevent someone from completing an intent." }, 
    ];

    const values = [
        { name: "Active", url: "None", description: "Active: Whether you prefer physical motion or not. We have three values: “inactive”(😴), “neutral”(🧘) and “active”(🏃). " },
        { name: "Social", url: "None", description: "Social: Whether you prefer social interaction or not. We have three values: “unsocial”(🫣), “neutral”(😐) and “social”(🤗)." },
        { name: "Helpful", url: "None", description: "Helpful: Whether you want to help others or not. We have four values: “harmful”(😈), “unhelpful”(🙅🏻‍♀️), “helpful”(👼) and “very helpful”(👼👼)." },
    ]

    const QA = [
        { name: "智能体的手里可以同时拿多个物体吗？", url: "None", description: "智能体的手里可以同时拿多个物体吗？: 智能体的手里可以同时拿多个物体，在手里已经有物体的情况下依然可以继续拿取(“Grab”)新的物体。" },
        { name: "容器里可以放多个物体吗？", url: "None", description: "容器里可以放多个物体吗？: 容器（Container， 比如box和shelf）里可以同时放多个物体。" },
        { name: "为什么半透明的物体在我看到它时消失了？", url: "None", description: "为什么半透明的物体在我看到它时消失了？: 物体是半透明表示在你的记忆中物体曾经在这个位置，而当你看向它时发现它已经不在这里了，所以会消失。" },
        { name: "为什么我视野中的智能体突然消失了？", url: "None", description: "为什么我视野中的智能体突然消失了？: 这是因为他离开了你的视线，你无法确定他到底去哪了。" },
        { name: "为什么我手里突然多了个物体/观测到物理状态的变化？", url: "None", description: "为什么我手里突然多了个物体/观测到物理状态的变化？: 在我们的游戏中，只有智能体才能改变物体的状态。如果你发现物体状态突然变化却没观测到智能体的动作，很可能是其他智能体在你的视线外做了相应的动作。" },
        { name: "为什么我的信念中突然多了个半透明的智能体？", url: "None", description: "为什么我的信念中突然多了个半透明的智能体？: 这是因为他做了一些主动的动作（如说话）让你可以判别他的位置。" },
        { name: "在玩这个游戏的时候我应该专注于完成任务还是要尽可能契合价值？", url: "None", description: "在玩这个游戏的时候我应该专注于完成任务还是要尽可能契合价值？: 1. 当自己的角色人设和完成给定的初始意图之间没有矛盾的时候，请根据自己的人设完成给定的初始意图。2. 当自己的角色人设和完成给定的初始意图之间有矛盾的时候，要代入角色和情境去思考，做出合理的决策即可。" },
        { name: "我应该怎么估计他人的意图？", url: "None", description: "我应该怎么估计他人的意图？: 你只需要写你所能估计出来的另一个智能体的最高层意图而不是较低层的子意图。例如：如果你估计 agent 2 的低层意图是 ['Open','box_2']，背后的高层意图是 ['Get','books_3', 'box_2']，即 agent 2 之所以想打开 box_2 是为了从box_2拿出books_3，那你就写 agent_2 的意图是 ['Get', 'books_3', 'box_2']，不要写 ['Open','box_2']。" },
        { name: "当我无法估计他人意图时，我该怎么做？", url: "None", description: "当我无法估计他人意图时，我该怎么做？: 如果您你全不知道，就选择“NA”。" },
        { name: "当我觉得他的意图有很多种可能时，我该怎么做？", url: "None", description: "当我觉得他的意图有很多种可能时，我该怎么做？: 选择最可能的一个作为猜测。" },
        { name: "我该如何更新我的意图？", url: "None", description: "我该如何更新我的意图？: 1. 当小黄人价值分布为 unsocial、inactive，且存在初始意图时，此时应该如何更新意图；\n a) 更看重 social 维度的价值，不寻求协助小黄人自己独立地完成；\n b) 更看重 active 维度的价值，尝试寻求帮助完成意图；\n c) 更看重价值，而非初始意图，更新意图为 none；\n 2. 当小黄人价值分布为 social、 inactive，且存在初始意图，此时如果估计出对方是 unhelpful，应该如何更新意图；\n a) 更看重 active 维度的价值，而非初始意图，更新意图为 none；\n b) 更看重意图的实现，小黄人自己独立地完成；\n 3. 当小黄人价值分布为 very helpful, unsocial, inactive，且无初始意图，此时猜测出对方在寻找某样物品，小黄人又知道物品在哪，应该如何更新意图；\n a) 更看重 helpful 以及 social 维度的价值，帮助对方且通过 active 即小黄人的非 social 动作完成帮助；\n b) 更看重 helpful 以及 active 维度的价值，帮助对方且通过 social 即小黄人的 social 动作完成帮助。" },
        { name: "当我的意图和价值冲突时，我该怎么做？", url: "None", description: "当我的意图和价值冲突时，我该怎么做？: 当小黄人的价值分布和小黄人的当前意图产生冲突时，您可以选择对意图作出合理的调整，也可以选择坚持当前意图；只要您完全投入您的角色并结合具体情境去思考并做出合理的决策即可。" },
        { name: "我该如何自由地移动到任何一个位置？", url: "None", description: "我该如何自由地移动到任何一个位置？: 当选择MoveTo, RotateTo这两个动作时，你可以通过点击屏幕来选择自己要移动到的位置/转向的角度。" },
        { name: "游戏什么时候会结束？", url: "None", description: "游戏什么时候会结束？: 当游戏达到最终轮数或者你与另一个智能体都达到了自己的初始意图时，游戏结束。" },
        { name: "我该如何获得奖励？", url: "None", description: "我该如何获得奖励？: 1. 充分投入地扮演好自己的角色，带着角色的初始意图设定（如果有）和角色的价值设定去行动，设身处地地给出合理的选择。2. 当自己的角色人设和完成给定的初始意图之间有矛盾的时候，要代入角色和情境去思考，做出合理的决策即可。" },

    ]

    // const categories = [
    //     { title: "Active Level 1", indexes: [0, 3, 4, 14] },
    //     { title: "Active Level 2", indexes: [9, 11, 15, 17, 19, 20, 21] },
    //     { title: "Active Level 3", indexes: [1, 5, 6, 10, 12, 13, 16, 18] },
    //     { title: "Active Level 4", indexes: [2, 7, 8] },
    // ];

    const categories = [
        {title: "All actions", indexes: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]}, 
        {title: "All intents", indexes: [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113]}, 
        {title: "All values", indexes: [200, 201, 202]},
        {title: "常见问题", indexes: [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314]}
    ]

    const nav = document.querySelector('.mysidebar');
    const gallery = document.querySelector('.gallery');

    const gallery_gif = document.getElementById('gallery_gif');
    const gallery_intent = document.getElementById('gallery_intent');
    const gallery_value = document.getElementById('gallery_value');
    const gallery_qa = document.getElementById('gallery_qa');

    const nav_gif = document.getElementById('sidebar_action');
    const nav_intent = document.getElementById('sidebar_intent');
    const nav_value = document.getElementById('sidebar_value');
    const nav_qa = document.getElementById('sidebar_qa');

    const gallery_dict = {
        "gallery_gif": gallery_gif, 
        "gallery_intent": gallery_intent, 
        "gallery_value": gallery_value, 
        "gallery_qa": gallery_qa, 
    }

    const nav_dict = {
        "nav_gif": nav_gif, 
        "nav_intent": nav_intent, 
        "nav_value": nav_value, 
        "nav_qa": nav_qa, 
    }

    // 创建一个函数来处理所有类别的创建
    function createCategories(categories, nav_dict, gallery_dict) {
        categories.forEach(category => {
            createCategoryItem(category.title, category.indexes, nav_dict, gallery_dict);
        });
    }

    // 创建单个类别和其子项的函数保持不变
    function createCategoryItem(title, indexes, nav_dict, gallery_dict) {
        const categoryItem = document.createElement('li');
        categoryItem.textContent = title;
        categoryItem.style.fontSize = '2em';
        categoryItem.style.color = "white"; 
        // nav.appendChild(categoryItem);

        const childContainer = document.createElement('ul');
        childContainer.style.display = 'block'; // 默认显示子元素
        categoryItem.appendChild(childContainer);

        indexes.forEach(index => {
            let gif; 
            if (index >= 300) {
                gif = QA[index - 300]; 
            }
            else if (index >= 200) {
                gif = values[index - 200]; 
            }
            else if (index >= 100 ) {
                gif = intents[index - 100]; 
            }
            else {
                gif = gifs[index];
            }
            const listItem = document.createElement('li');
            
            listItem.textContent = gif.name;
            listItem.style.fontSize = '1em';
            listItem.style.color = "white"; 
            listItem.onclick = (event) => {
                highlightGif(index);
                event.stopPropagation();  // 阻止事件冒泡
            };
            childContainer.appendChild(listItem);

            const gifItem = document.createElement('div');
            gifItem.classList.add('gif-item');
            gifItem.id = `gif-${index}`;
            // const formattedDescription = gif.description.replace(/: /, ': \n');

                // 分解description为命令和解释，添加颜色
            const parts = gif.description.split(': ');
            const command = parts[0];
            let explanation
            if (parts.length == 2){
                explanation = parts[1];
            }
            else if (parts.length == 3){
                explanation = parts[1] + parts[2];
            }
            
            const formattedDescription = `<span class="command">${command}</span> \n <span class="explanation">${explanation}</span>`;

            if (gif.url == "None"){
                gifItem.innerHTML = `<p>${formattedDescription}</p>`;
                if (index >= 300) {
                    gallery_dict["gallery_qa"].appendChild(gifItem)
                    nav_dict["nav_qa"].appendChild(categoryItem);
                }
                else if (index >= 200) {
                    gallery_dict["gallery_value"].appendChild(gifItem)
                    nav_dict["nav_value"].appendChild(categoryItem);
                }
                else {
                    gallery_dict["gallery_intent"].appendChild(gifItem)
                    nav_dict["nav_intent"].appendChild(categoryItem);
                }
            }
            else {
                gifItem.innerHTML = `<img src="${gif.url}" alt="${gif.name}"><p>${formattedDescription}</p>`;
                gallery_dict["gallery_gif"].appendChild(gifItem)
                nav_dict["nav_gif"].appendChild(categoryItem);
            }

            const descriptionElement = gifItem.querySelector('p');
            if (descriptionElement) {
                descriptionElement.style.fontSize = '1.2em';
                descriptionElement.style.whiteSpace = 'pre-wrap';
            }
        });

        categoryItem.onclick = () => {
            const isVisible = categoryItem.getAttribute('data-visible') === 'true';
            childContainer.style.display = isVisible ? 'none' : 'block';
            categoryItem.setAttribute('data-visible', isVisible ? 'false' : 'true');
        };
    }

    function highlightGif(index) {
        document.querySelectorAll('.gif-item').forEach(item => item.classList.remove('active'));
        document.querySelector(`#gif-${index}`).classList.add('active');
        // 滚动到指定的GIF
        document.querySelector(`#gif-${index}`).scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // 示例使用
    createCategories(categories, nav_dict, gallery_dict);

});

// 获取按钮元素
var backToTopBtn = document.getElementById("backToTopBtn");

// 当用户滚动时，检测页面的滚动位置
window.onscroll = function() {
    scrollFunction();
};

function scrollFunction() {
    // 当页面向下滚动超过100px时，显示按钮
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        backToTopBtn.style.display = "block";
    } else {
        backToTopBtn.style.display = "none";
    }
}

// 当用户点击按钮时，滚动回到页面顶部
backToTopBtn.onclick = function() {
    // 使用平滑滚动
    window.scrollTo({top: 0, behavior: 'smooth'});
};