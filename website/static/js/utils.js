

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function getAbsoluteHeight(el) {
    // Get the DOM Node if you pass in a string
    el = (typeof el === 'string') ? document.querySelector(el) : el;

    var styles = window.getComputedStyle(el);
    var margin = parseFloat(styles['marginTop']) + parseFloat(styles['marginBottom']);

    return Math.ceil(el.offsetHeight + margin);
}

function isArrayEqual(arr1, arr2) {
  if (arr1.length !== arr2.length) {
    return false;
  }

  for (let i = 0; i < arr1.length; i++) {
    if (!isDeepEqual(arr1[i], arr2[i])) {
      return false;
    }
  }

  return true;
}

function isDeepEqual(obj1, obj2) {
  if (obj1 === obj2) {
    return true;
  }

  if (typeof obj1 !== 'object' || typeof obj2 !== 'object') {
    return false;
  }

  if (Array.isArray(obj1) && Array.isArray(obj2)) {
    return isArrayEqual(obj1, obj2);
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) {
    return false;
  }

  for (const key of keys1) {
    if (!keys2.includes(key) || !isDeepEqual(obj1[key], obj2[key])) {
      return false;
    }
  }

  return true;
}


function updateValue(id, value) {
    document.getElementById(id).innerText = value;
}


function toggleValuesVisibility(showFlag) {
    var name12 = document.getElementById('name12');
    var activeLabel = document.querySelector('label[for="sel_other_desire_active"]');
    var activeValue = document.getElementById('active-value');
    var socialLabel = document.querySelector('label[for="sel_other_desire_social"]');
    var socialValue = document.getElementById('social-value');
    var helpfulLabel = document.querySelector('label[for="sel_other_desire_helpful"]');
    var helpfulValue = document.getElementById('helpful-value');

    var activeField = document.getElementById('sel_other_desire_active');
    var socialField = document.getElementById('sel_other_desire_social');
    var helpfulField = document.getElementById('sel_other_desire_helpful');

    var bottomLabels = document.getElementById('labels');
    const valueSpans = document.querySelectorAll('.value-span');


    if (showFlag) {
        name12.style.display = 'block';
        activeLabel.style.display = 'inline';
        socialLabel.style.display = 'inline';
        helpfulLabel.style.display = 'inline';

        activeField.style.display = 'inline';
        socialField.style.display = 'inline';
        helpfulField.style.display = 'inline';

        valueSpans.forEach(span => {
            span.style.display = 'inline';
        });
    } else {
        name12.style.display = 'none';

        valueSpans.forEach(span => {
            span.style.display = 'none';
        });

        activeLabel.style.display = 'none';
        activeValue.style.display = 'none';
        socialLabel.style.display = 'none';
        socialValue.style.display = 'none';
        helpfulLabel.style.display = 'none';
        helpfulValue.style.display = 'none';

        activeField.style.display = 'none';
        socialField.style.display = 'none';
        helpfulField.style.display = 'none';

        //bottomLabels.style.height = '18vh'; // 设置一个合适的固定高度
    }
}


function transformActionOptionDict(action_option_dict) {
    for (var key in action_option_dict) {
        if (action_option_dict.hasOwnProperty(key)) {
            action_option_dict[key] = action_option_dict[key].map(function(pairsList) {
                 return pairsList.map(function(pair) {
//                    if (pair[0] == "Hello!" || pair[0] == "Thank you!" || pair[0] == 'eat' || pair[0] == 'drink')  {
                    if (["Hello!", "Thank you!", 'eat', 'drink', 'X: Y: '].includes(pair[0]))  {
                        return [pair[0], pair[0]];
                    } else  {
                      if (!pair[0].startsWith('agent')) {
                          return [pair[0] + "_" + pair[1].toString(), pair[1]];
                      } 
                      else {
                        return [pair[0], pair[1]];
                      } 
                    }
                  }); 
             }
            );
        }
    }
    return action_option_dict;
}

let isMarkerVisible = false;

function displayClickMarker(x, y, offsetX, offsetY) {
    let marker = document.getElementById('click-marker');
    if (!marker) {
        marker = document.createElement('div');
        marker.id = 'click-marker';
        marker.style.position = 'absolute';
        marker.style.border = '2px solid red';
        marker.style.borderRadius = '50%';
        marker.style.width = '10px';
        marker.style.height = '10px';
        marker.style.pointerEvents = 'none'; // 避免影响鼠标事件
        document.body.appendChild(marker);
    }
    marker.style.left = `${x + offsetX - 5}px`; // -5 是为了居中标记
    marker.style.top = `${y + offsetY - 5}px`;
    marker.style.display = 'block'; // 显示标记
}


function onMouseMove(event) {
    const img = document.getElementById('render');
    const rect = img.getBoundingClientRect();

    const selectedAction = document.getElementById("sel_action").value;
    const divDisplay = document.getElementById("2.3").style.display;
    if (divDisplay !== 'none' && (selectedAction === 'ActionRotateTo' || selectedAction === 'ActionMoveTo')) {
        const x = Math.floor(event.clientX - rect.left);
        const y = Math.floor(event.clientY - rect.top);
        // 更新鼠标移动的实时标记位置
        if (!isMarkerVisible) {
            displayClickMarker(x, y, rect.left, rect.top);
        }
    } else {
        hideClickMarker();
    }
}

function hideClickMarker() {
    let marker = document.getElementById('click-marker');
//    if (marker && !isMarkerVisible) {
    if (marker) {
        marker.style.display = 'none';
    }
}

function getClickPosition(event) {
    const img = document.getElementById('render');
    const rect = img.getBoundingClientRect();

    const x = Math.floor(event.clientX - rect.left);
    const y = Math.floor(event.clientY - rect.top);

    const xRatio = (x / rect.width).toFixed(2);
    const yRatio = (y / rect.height).toFixed(2);

    console.log("mouse click at, x: " + x + " y: " + y);

    const selectedAction = document.getElementById("sel_action").value;
    const divDisplay = document.getElementById("2.3").style.display;
    if (divDisplay !== 'none' && (selectedAction === 'ActionRotateTo' || selectedAction === 'ActionMoveTo')) {
        const select1 = document.getElementById("sel_action_para1");
        const select2 = document.getElementById("sel_action_para2");

        // 覆盖 X 选项
        let optionExists = false;
        for (let i = 0; i < select1.options.length; i++) {
            if (select1.options[i].text.startsWith("X:")) {
                select1.options[i] = new Option(`X: ${x}, Y: ${y}`, `${xRatio},${yRatio}`);
                optionExists = true;
                break;
            }
        }
        if (!optionExists) {
            select1.options.add(new Option(`X: ${x}, Y: ${y}`, `${xRatio},${yRatio}`));
        }
        select1.value = `${xRatio},${yRatio}`;
        select1.disabled = false;
        select2.disabled = true;

        displayClickMarker(x, y, rect.left, rect.top);
        isMarkerVisible = true;
    }
}


function ZoomImage(iteration) {
    // 三个 desire 图片 popup
    var desireImgs = document.querySelectorAll('.image');
        if (iteration % 3 == 0) {
            for (img of desireImgs) {
                img.classList.add('zoom');
            }
        } else {
            for (img of desireImgs) {
                img.classList.remove('zoom');
            }
        }
}


function checkSid() {
    const sid = document.cookie.match(/sid=([^;]+)/);
    console.log('current sid:', sid ? sid[1] : 'Not found');
}

window.onerror = function(message, source, lineno, colno, error) {
    console.error("Caught error:", error);
    // 可以发送错误信息到服务器
};