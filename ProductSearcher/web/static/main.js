/*
 *  Product Searcher Viewer JS
 */

function ready(fn){
    if (document.readyState === "complete" || document.readyState === "interactive") {
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

ready(function(){

    add_platforms()

    let suggest_debounce = _.debounce(suggest, 1000);

    document.getElementById('search-input').addEventListener('keypress', function (e) {
        let key = e.which || e.keyCode;
        if (key === 13) {
            search()
        }
        else{
            suggest_debounce()
        }
    })

    document.getElementById('search-input-icon').addEventListener('click', function(){
        search()
    })
})

function add_platforms(){
    let search_platforms = [
        {name: 'etsy', value: 'etsy'},
        {name: 'nytimes', value: 'nytimes'},
        {name: 'uncommongoods', value: 'uncommongoods'},
        {name: 'citizenry', value: 'citizenry'}
    ]

    let search_platforms_html = '';

    search_platforms.forEach(platform => search_platforms_html += generatePlatformHtml(platform))

    document.getElementById('search-platforms').innerHTML = search_platforms_html
}

function search(){
    let url = new URL('/search', document.URL)

    let search_key = document.getElementById('search-input').value

    if(search_key == "")
        return

    let search_platforms = document.getElementById('search-platforms').querySelectorAll('input[type="checkbox"]:checked')
    search_platforms = Array.prototype.map.call(search_platforms, platform => {return platform.value}).join(',')

    let expected_price = document.getElementById('expected-price').value

    let params = {
        search_key: search_key,
        search_platforms: search_platforms,
        expected_price: expected_price,
    }

    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

    let spinner = document.getElementById('search-spinner')
    let reuslt_container = document.getElementById('search-product-reuslt')

    reuslt_container.innerHTML = "";

    spinner.toggleAttribute('hidden')

    fetch(url)
        .then(function(response) {

            spinner.toggleAttribute('hidden')

            if(response.ok) {
                return response.json();
            }

            throw new Error('Seacrh fail.');
        })
        .then(function(product_list) {

            let product_list_html = ""

            product_list.forEach(function(product){
                product_list_html = product_list_html + generateProductCardHtml(product)
            })

            reuslt_container.innerHTML = product_list_html
        })
        .catch(function(error) {
            console.log(error.message);
        });
}

function suggest(){
    let url = new URL('/suggest', document.URL)

    let search_key = document.getElementById('search-input').value

    if(search_key == "")
        return

    let params = {
        search_key: search_key,
    }

    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

    let suggest_list_dom = document.getElementById('search-suggest')
    suggest_list_dom.innerHTML = ''

    fetch(url)
        .then(function(response) {

            if(response.ok) {
                return response.json();
            }

            throw new Error('Suggest fail.');
        })
        .then(function(suggest_list) {

            let suggest_list_html = ""

            suggest_list.forEach(function(suggest_word){
                suggest_list_html = suggest_list_html + generateSuggestWordHtml(suggest_word)
            })

            suggest_list_dom.innerHTML = suggest_list_html
        })
        .catch(function(error) {
            console.log(error.message);
        });
}

function toggle_checkbox(evt){
    evt = evt || window.event;
    let label = evt.target || evt.srcElement;
    let checkbox = label.previousSibling
    console.log(label)
    console.log(label.previousSibling)
    if (checkbox.hasAttribute('checked')) {
        checkbox.removeAttribute('checked')
    }else{
        checkbox.setAttribute('checked', '')
    }
}

function generatePlatformHtml(platform){
    return `<span class="color-gold" onclick="toggle_checkbox()"><input class="uk-checkbox" type="checkbox" value="${platform['value']}" checked><label class="paltform-checkbox-label">${platform['name']}</label></span>`
}


function generateProductCardHtml(product){
    return `<div class="uk-card">
                <div class="bg-color-white">
                    <div class="uk-card-media-top">
                        <a href="${product['product_link']}" target="_blank"><img data-src="${product['product_image']}" uk-img></a>
                    </div>
                    <div class="uk-card-body">
                        <div class="uk-grid-small uk-child-width-1-1@s" uk-grid>
                            <a class="a-normal" href="${product['product_link']}" target="_blank"><div class="uk-text-truncate">${product['product_name']}</div></a>
                            <div>$${product['product_price']}</div>
                        </div>
                    </div>
                </div>
            </div>`
}

function generateSuggestWordHtml(suggest_word){
    return `<option>${suggest_word}</option>`
}
