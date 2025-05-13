
function decideValueBars(active, social, helpful) {
    // 清除所有之前的高亮
    clearAllHighlights();

    // 决定 active 值的高亮
    if (active <= 0) {
        highlightElement('Active', 0);
    } else if (active <= 0.5) {
        highlightElement('Active', 1);
    } else {
        highlightElement('Active', 2);
    }

    // 决定 social 值的高亮
    if (social <= 0) {
        highlightElement('Social', 0);
    } else if (social <= 0.5) {
        highlightElement('Social', 1);
    } else {
        highlightElement('Social', 2);
    }

    // 决定 helpful 值的高亮
    if (helpful <= -1) {
        highlightElement('Helpful', 0);
    } else if (helpful <= 0) {
        highlightElement('Helpful', 1);
    } else if (helpful <= 1) {
        highlightElement('Helpful', 2);
    } else {
        highlightElement('Helpful', 3);
    }
}

function clearAllHighlights() {
    const allEmojis = document.querySelectorAll('.side-emoji');
    const allLabels = document.querySelectorAll('.side-label');
    allEmojis.forEach(emoji => {
        emoji.style.backgroundColor = '';
        emoji.style.borderRadius = '';
        emoji.style.padding = '';
    });
    allLabels.forEach(label => label.style.color = '');
}

function highlightElement(type, index) {
    const HIGHLIGHT_COLOR = 'rgba(10, 115, 255, 1)';
    const desireItems = document.querySelectorAll('.desire-item');
    for (let item of desireItems) {
        const titleSpan = item.querySelector('.text-container span:first-child');
        if (titleSpan && titleSpan.textContent.trim() === type) {
            const scalePoints = item.querySelectorAll('.scale-point');
            if (scalePoints.length > index) {
                const emoji = scalePoints[index].querySelector('.side-emoji');
                const label = scalePoints[index].querySelector('.side-label');
                if (emoji) {
                    emoji.style.backgroundColor = HIGHLIGHT_COLOR;
                    // 检查 emoji 的宽度，决定使用圆形还是椭圆形背景
                    if (emoji.offsetWidth > emoji.offsetHeight * 1.2) {
                        // 如果宽度明显大于高度，使用椭圆形
                        emoji.style.borderRadius = '1em';
                    } else {
                        // 否则使用圆形
                        emoji.style.borderRadius = '50%';
                        emoji.style.aspectRatio = '1 / 1';
                    }
                    // 确保 padding 足够包围 emoji
//                    emoji.style.padding = '0.2em 0.3em';
                }
                if (label) label.style.color = HIGHLIGHT_COLOR;
            }
            break;
        }
    }
}



function getDesireValue(selector) {
    // 检查元素的 display 属性是否为 none
    if ($(selector).css('display') !== 'none') {
        return $(selector).val();
    }
    return '';
}

function setAgentNamePosition(containerId, position) {
  const container = document.getElementById(containerId);
  const agentName = container.querySelector('.agent-name');

  if (position === 'up') {
    agentName.classList.add('name-down');
    agentName.classList.remove('name-up');
  } else if (position === 'down') {
    agentName.classList.add('name-up');
    agentName.classList.remove('name-down');
  }
}

function setEmojiPositionForAgent(userAgentId, agentId, position, renderElement) {
    const emojiContainer = document.getElementById('emoji-container-' + agentId);

    // 计算目标位置相对于 renderElement 的位置
    const emojiX = position.x_ratio * renderElement.clientWidth;
    const emojiY = position.y_ratio * renderElement.clientHeight;

    // 获取 renderElement 的位置信息
    const renderRect = renderElement.getBoundingClientRect();

    requestAnimationFrame(() => {
        const emojiContainerRect = emojiContainer.getBoundingClientRect();
        const emojiContainerWidth = emojiContainerRect.width;
        const emojiContainerHeight = emojiContainerRect.height;

        // 计算中上位置，并相对于 renderRect 进行调整
        const newX = emojiX - emojiContainerWidth / 2;
        let newY;
        if (position.direction == 'up') {
            newY = emojiY;
        } else {
            newY = emojiY - emojiContainerHeight;
        }

        // 设置 emojiContainer 的位置，以中上对齐
        emojiContainer.style.left = `${newX}px`;
        emojiContainer.style.top = `${newY}px`;
        emojiContainer.style.visibility = 'visible';

        var agentNameElement = emojiContainer.querySelector('.agent-name');
        if (agentNameElement && agentId != userAgentId) {
            agentNameElement.textContent = 'agent ' + agentId;
            agentNameElement.style.display = 'block';
            if (position.direction == 'up') {
                setAgentNamePosition('emoji-container-' + agentId, 'up');
            } else {
                setAgentNamePosition('emoji-container-' + agentId, 'down');
            }
        }
    });

}

function setEmojiPosition(userAgentId, valuesPosRatio) {
    // for rendering test clear the position data
//    valuesPosRatio = {};
    const renderElement = document.getElementById('render');
    for (const agentId in valuesPosRatio) {
        const position = valuesPosRatio[agentId];
        if (!('x_ratio' in position)) {
            const emojiContainer = document.getElementById('emoji-container-' + agentId);
            emojiContainer.style.visibility = 'hidden';
            var agentNameElement = emojiContainer.querySelector('.agent-name');
            if (agentNameElement) {
                agentNameElement.style.display = 'none';
            }
            continue;
        }
        setEmojiPositionForAgent(userAgentId, agentId, position, renderElement);
    }
}

function decideValueEmoji(agentId, active, social, helpful) {
    const container = document.getElementById('emoji-container-' + agentId);
    const activeEmoji = container.querySelector(`.emoji[data-attribute="active"]`);
    const socialEmoji = container.querySelector(`.emoji[data-attribute="social"]`);
    const helpfulEmoji = container.querySelector(`.emoji[data-attribute="helpful"]`);

    if (active <= 0) {
        activeEmoji.textContent = '😴‍';
    } else if (active <= 0.5) {
        activeEmoji.textContent = '🧘';
    } else {
        activeEmoji.textContent = '🏃';
    }

    if (social <= 0) {
        socialEmoji.textContent = '🫣';
    } else if (social <= 0.5) {
        socialEmoji.textContent = '😐';
    } else {
        socialEmoji.textContent = '🤗';
    }

    if (helpful <= -1) {
        helpfulEmoji.textContent = '😈';
    } else if (helpful <= 0) {
        helpfulEmoji.textContent = '🙅🏻‍♀️';
    } else if (helpful <= 1) {
        helpfulEmoji.textContent = '👼';
    } else {
        helpfulEmoji.textContent = '👼👼';
    }
}
