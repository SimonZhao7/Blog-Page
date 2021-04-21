function showCreate()
{
    var formItems = [...document.getElementsByClassName('create-form-popup')];
    var background = document.getElementById("dimmer");
    for (var i = 0; i < formItems.length; i++)
    {
        formItems[i].style.display = "block";
    }
    background.style.display = "block";
}

function hideCreate()
{
    var formItems = [...document.getElementsByClassName('create-form-popup')];
    var background = document.getElementById("dimmer");
    for (var i = 0; i < formItems.length; i++)
    {
        formItems[i].style.display = "none";
    }
    background.style.display = "none";
}