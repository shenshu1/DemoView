/* ==========================================================================
   🌌 Address Recreation JS - High Fidelity Logic
   ========================================================================== */

// ─── 1. Mock Chinese Address Database ──────────────────────────────────────────
const ADDRESS_DATA = {
    "广东省": {
        "深圳市": ["南山区", "福田区", "罗湖区", "宝安区", "龙华区", "龙岗区"],
        "广州市": ["天河区", "越秀区", "白云区", "番禺区", "海珠区", "荔湾区"],
        "珠海市": ["香洲区", "斗门区", "金湾区"]
    },
    "北京市": {
        "北京市": ["东城区", "西城区", "朝阳区", "海淀区", "丰台区", "石景山区"]
    },
    "上海市": {
        "上海市": ["黄浦区", "徐汇区", "静安区", "浦东新区", "长宁区", "普陀区"]
    },
    "浙江省": {
        "杭州市": ["西湖区", "滨江区", "拱墅区", "萧山区", "余杭区"],
        "宁波市": ["海曙区", "江北区", "鄞州区"],
        "温州市": ["鹿城区", "龙湾区", "瓯海区"]
    },
    "四川省": {
        "成都市": ["锦江区", "青羊区", "金牛区", "武侯区", "成华区", "高新区"],
        "绵阳市": ["涪城区", "游仙区", "安州区"]
    }
};

// ─── Mock Address Results (for the address selection page) ──────────────────
const MOCK_ADDRESS_RESULTS = {
    "深圳": [
        { name: "龙华区数字创新中心", detail: "民塘路与白松路交叉口东60米", active: true },
        { name: "鸿荣源北站中心A座", detail: "民塘路328号" },
        { name: "鸿荣源·天俊", detail: "民治街道民塘路" },
        { name: "鸿荣源北站中心B座", detail: "民塘路328号" },
        { name: "壹号写字楼", detail: "白松路与新治路交叉口东北100米" },
        { name: "龙华区政务服务中心", detail: "清龙路8号" },
        { name: "深圳北站", detail: "致远中路28号" },
        { name: "龙华文化广场", detail: "东环一路与和平路交叉口西北角" },
    ],
    "广州": [
        { name: "天河城购物中心", detail: "天河路208号", active: true },
        { name: "珠江新城", detail: "花城大道" },
        { name: "广州塔", detail: "阅江西路222号" },
        { name: "正佳广场", detail: "天河路228号" },
        { name: "太古汇", detail: "天河路383号" },
    ],
    "北京": [
        { name: "国贸大厦", detail: "建国门外大街1号", active: true },
        { name: "王府井步行街", detail: "王府井大街" },
        { name: "中关村科技园", detail: "海淀区中关村南大街" },
        { name: "三里屯太古里", detail: "三里屯路19号" },
    ],
    "上海": [
        { name: "陆家嘴金融中心", detail: "世纪大道88号", active: true },
        { name: "南京东路步行街", detail: "南京东路" },
        { name: "外滩", detail: "中山东一路" },
        { name: "徐家汇商圈", detail: "漕溪北路" },
    ],
    "杭州": [
        { name: "西湖文化广场", detail: "武林广场21号", active: true },
        { name: "阿里巴巴西溪园区", detail: "文一西路969号" },
        { name: "钱江新城", detail: "富春路" },
    ],
    "成都": [
        { name: "春熙路商圈", detail: "春熙路", active: true },
        { name: "天府广场", detail: "人民西路" },
        { name: "太古里", detail: "中纱帽街8号" },
    ],
};

// City to province/city mapping
const CITY_MAP = {
    "深圳": { province: "广东省", city: "深圳市" },
    "广州": { province: "广东省", city: "广州市" },
    "珠海": { province: "广东省", city: "珠海市" },
    "北京": { province: "北京市", city: "北京市" },
    "上海": { province: "上海市", city: "上海市" },
    "杭州": { province: "浙江省", city: "杭州市" },
    "宁波": { province: "浙江省", city: "宁波市" },
    "温州": { province: "浙江省", city: "温州市" },
    "成都": { province: "四川省", city: "成都市" },
    "绵阳": { province: "四川省", city: "绵阳市" },
};

// ─── 2. State Variables ───────────────────────────────────────────────────────
let currentProvince = "";
let currentCity = "";
let currentDistrict = "";
let isDefaultAddress = false;
let selectedAddrCity = "深圳";

// ─── 3. DOM Elements ──────────────────────────────────────────────────────────
const receiverNameInput = document.getElementById("receiverName");
const receiverPhoneInput = document.getElementById("receiverPhone");
const regionText = document.getElementById("regionText");
const detailAddressInput = document.getElementById("detailAddress");
const parserInput = document.getElementById("parserInput");
const defaultCheckbox = document.getElementById("defaultCheckbox");
const defaultToggle = document.getElementById("defaultToggle");
const addressPickerTrigger = document.getElementById("addressPickerTrigger");
const tooltip = document.getElementById("tooltip");
const locationBtn = document.getElementById("locationBtn");
const identifyBtn = document.getElementById("identifyBtn");
const saveBtn = document.getElementById("saveBtn");
const addressForm = document.getElementById("addressForm");

// Address Page Overlay Elements
const addressPageOverlay = document.getElementById("addressPageOverlay");
const addrBackBtn = document.getElementById("addrBackBtn");
const addrCloseBtn = document.getElementById("addrCloseBtn");
const addrResultsList = document.getElementById("addrResultsList");
const addrSearchInput = document.getElementById("addrSearchInput");
const addrCitySelector = document.getElementById("addrCitySelector");
const addrCityText = document.getElementById("addrCityText");

// Toast Notification
const toast = document.getElementById("toast");

// WeChat UI Mock Elements
const closeBtn = document.getElementById("closeBtn");
const backNavBtn = document.getElementById("backNavBtn");

// ─── 4. Helper: Custom Toast ──────────────────────────────────────────────────
function showToast(message, duration = 2000) {
    toast.textContent = message;
    toast.classList.add("show");
    
    setTimeout(() => {
        toast.classList.remove("show");
    }, duration);
}

// ─── 5. UI Toggles & Simple Actions ──────────────────────────────────────────

// Hide tooltip after first click on region selector
addressPickerTrigger.addEventListener("click", () => {
    if (tooltip) {
        tooltip.style.opacity = "0";
        setTimeout(() => tooltip.remove(), 300);
    }
});

// Toggle Default Address Checkbox
defaultToggle.addEventListener("click", () => {
    isDefaultAddress = !isDefaultAddress;
    defaultCheckbox.classList.toggle("checked", isDefaultAddress);
});

// Mock WeChat actions
closeBtn.addEventListener("click", () => {
    showToast("已退出该应用页面");
});

backNavBtn.addEventListener("click", () => {
    showToast("返回上一页");
});

// ─── 6. Full-page Address Selection ─────────────────────────────────────────

function openAddressPage() {
    addressPageOverlay.classList.add("show");
    renderAddressResults(selectedAddrCity);
}

function closeAddressPage() {
    addressPageOverlay.classList.remove("show");
}

function renderAddressResults(city, filter = "") {
    addrResultsList.innerHTML = "";
    const results = MOCK_ADDRESS_RESULTS[city] || [];
    
    const filtered = filter
        ? results.filter(r => r.name.includes(filter) || r.detail.includes(filter))
        : results;
    
    if (filtered.length === 0) {
        const emptyLi = document.createElement("li");
        emptyLi.style.padding = "40px 16px";
        emptyLi.style.textAlign = "center";
        emptyLi.style.color = "#999";
        emptyLi.style.fontSize = "14px";
        emptyLi.textContent = "暂无搜索结果";
        addrResultsList.appendChild(emptyLi);
        return;
    }
    
    filtered.forEach((addr, index) => {
        const li = document.createElement("li");
        li.className = `addr-result-item${addr.active ? ' active' : ''}`;
        li.innerHTML = `
            <div class="addr-result-dot"></div>
            <div class="addr-result-info">
                <div class="addr-result-name">${addr.name}</div>
                <div class="addr-result-detail">${addr.detail}</div>
            </div>
        `;
        li.addEventListener("click", () => selectAddress(city, addr, index));
        addrResultsList.appendChild(li);
    });
}

function selectAddress(city, addr, index) {
    // Update active state in mock data
    const results = MOCK_ADDRESS_RESULTS[city] || [];
    results.forEach(r => r.active = false);
    if (results[index]) results[index].active = true;
    
    // Map city to province/city
    const mapping = CITY_MAP[city];
    if (mapping) {
        currentProvince = mapping.province;
        currentCity = mapping.city;
        // Try to extract district from name
        const districts = ADDRESS_DATA[currentProvince]?.[currentCity] || [];
        currentDistrict = districts.find(d => addr.name.includes(d)) || districts[0] || "";
    }
    
    // Format: 省+市+详细地址+地标名
    // e.g. 广东省深圳市民塘路与白松路交叉口东60米龙华区数字创新中心
    const fullAddress = `${currentProvince}${currentCity}${addr.detail}${addr.name}`;
    regionText.textContent = fullAddress;
    regionText.classList.add("selected");
    
    // Close the address page
    closeAddressPage();
    showToast(`已选择: ${addr.name}`);
}

// Address picker label click -> open address page
addressPickerTrigger.addEventListener("click", (e) => {
    // Prevent opening if location button was clicked
    if (locationBtn.contains(e.target)) return;
    openAddressPage();
});

// Back button on address page
addrBackBtn.addEventListener("click", closeAddressPage);
addrCloseBtn.addEventListener("click", closeAddressPage);

// Search functionality
let searchTimeout = null;
addrSearchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = addrSearchInput.value.trim();
        renderAddressResults(selectedAddrCity, query);
    }, 300);
});

// City selector (simple toggle through available cities)
const availableCities = Object.keys(MOCK_ADDRESS_RESULTS);
addrCitySelector.addEventListener("click", () => {
    const currentIndex = availableCities.indexOf(selectedAddrCity);
    const nextIndex = (currentIndex + 1) % availableCities.length;
    selectedAddrCity = availableCities[nextIndex];
    addrCityText.textContent = selectedAddrCity;
    addrSearchInput.value = "";
    renderAddressResults(selectedAddrCity);
});

// ─── 7. Mock Location ("定位") Feature ──────────────────────────────────────────
locationBtn.addEventListener("click", (e) => {
    e.stopPropagation(); // Avoid triggering region selector
    
    showToast("获取 GPS 定位中...");
    locationBtn.style.pointerEvents = "none";
    locationBtn.querySelector("span").textContent = "定位中";
    
    setTimeout(() => {
        currentProvince = "广东省";
        currentCity = "深圳市";
        currentDistrict = "南山区";
        
        regionText.textContent = `${currentProvince}-${currentCity}-${currentDistrict}`;
        regionText.classList.add("selected");
        detailAddressInput.value = "科兴科学园B栋3单元1201室";
        
        locationBtn.style.pointerEvents = "auto";
        locationBtn.querySelector("span").textContent = "定位";
        
        showToast("已成功获取高精度定位！");
    }, 1200);
});

// ─── 8. Smart Regex Parser ("识别") Feature ────────────────────────────────────
identifyBtn.addEventListener("click", () => {
    const rawText = parserInput.value.trim();
    if (!rawText) {
        showToast("请先粘贴包含地址信息的文本");
        return;
    }
    
    // Parse name, phone, and address
    const result = parseAddressInfo(rawText);
    
    if (result.name || result.phone || result.address) {
        let fills = [];
        
        if (result.name) {
            receiverNameInput.value = result.name;
            fills.push("姓名");
        }
        if (result.phone) {
            receiverPhoneInput.value = result.phone;
            fills.push("手机号");
        }
        if (result.address) {
            // Attempt to separate region from detailed address
            const splitAddress = splitRegionAndDetail(result.address);
            if (splitAddress.region) {
                regionText.textContent = splitAddress.region;
                regionText.classList.add("selected");
                
                // Parse out active variables for picker sync
                const parts = splitAddress.region.split("-");
                currentProvince = parts[0] || "";
                currentCity = parts[1] || "";
                currentDistrict = parts[2] || "";
                
                fills.push("省市区");
            }
            if (splitAddress.detail) {
                detailAddressInput.value = splitAddress.detail;
                fills.push("详细地址");
            }
        }
        
        showToast(`智能识别成功，已填充: ${fills.join('、')}`);
    } else {
        showToast("无法识别有效信息，请检查粘贴的内容");
    }
});

/**
 * Parses a block of text to extract:
 * - Phone (11 digits starting with 1)
 * - Name (typically a short segment of 2-4 chars)
 * - Remaining string as Address
 */
function parseAddressInfo(text) {
    // 1. Phone matching: 11 digits starting with 1
    const phoneRegex = /(1[3-9]\d{9})/;
    const phoneMatch = text.match(phoneRegex);
    const phone = phoneMatch ? phoneMatch[0] : "";
    
    // Remove the phone number from the parsing source
    let cleaned = text.replace(phone, " ");
    
    // Replace commas, semicolons, brackets, spaces with whitespace dividers
    cleaned = cleaned.replace(/[,，;；\s\n\[\]()（）:\uff1a]/g, " ");
    
    // Split into segments
    const segments = cleaned.split(/\s+/).map(s => s.trim()).filter(Boolean);
    
    let name = "";
    let address = "";
    
    // Simple heuristic to identify name and address
    for (let seg of segments) {
        // Name check: 2-4 Chinese characters and not containing common address keywords
        if (!name && seg.length >= 2 && seg.length <= 4 && /^[\u4e00-\u9fa5]+$/.test(seg) && !/省|市|区|县|乡|镇|村|路|街|弄|号|室|楼|园|栋/.test(seg)) {
            name = seg;
        } else {
            // Address accumulator
            if (address) {
                address += " " + seg;
            } else {
                address = seg;
            }
        }
    }
    
    // Heuristic fallback if name is still empty (use first short segment)
    if (!name && segments.length > 0) {
        const firstChinese = segments.find(s => /^[\u4e00-\u9fa5]+$/.test(s) && s.length <= 4);
        if (firstChinese) {
            name = firstChinese;
            address = segments.filter(s => s !== name).join(" ");
        }
    }
    
    return { name, phone, address };
}

/**
 * Splits a full address string into region (Province-City-District) and detail address.
 */
function splitRegionAndDetail(fullAddress) {
    // Support regex for Chinese Administrative Division divisions
    // Supports matching:
    // xxx省/自治区 xxx市/自治州 xxx区/县/市
    const regionRegex = /^.*?(省|自治区|直辖市).*?(市|自治州|地区).*?(区|县|县级市|市|旗|盟|口)/;
    
    const match = fullAddress.match(regionRegex);
    
    if (match) {
        const rawRegion = match[0];
        const detail = fullAddress.replace(rawRegion, "").trim();
        
        // Formulate into Province-City-District format
        // Match capture groups to structure the dashes
        const structuredMatch = rawRegion.match(/^(.*?(省|自治区|直辖市))?\s*(.*?(市|自治州|地区))?\s*(.*?(区|县|县级市|市|旗|盟|口))?/);
        if (structuredMatch) {
            const prov = (structuredMatch[1] || "").trim();
            const city = (structuredMatch[3] || "").trim();
            const dist = (structuredMatch[5] || "").trim();
            
            // Clean up separator spaces
            return {
                region: [prov, city, dist].filter(Boolean).join("-"),
                detail: detail
            };
        }
    }
    
    // Fallback split based on common keywords
    // For direct city inputs like "深圳市南山区" without province
    const cityDistrictRegex = /^.*?(市|州).*?(区|县|市)/;
    const matchNoProv = fullAddress.match(cityDistrictRegex);
    if (matchNoProv) {
        const rawRegion = matchNoProv[0];
        const detail = fullAddress.replace(rawRegion, "").trim();
        
        // Try to find the province if it's one of our mock data
        let prov = "";
        let city = "";
        let dist = "";
        
        // Scan our database to match city and autofill province
        for (let p of Object.keys(ADDRESS_DATA)) {
            for (let c of Object.keys(ADDRESS_DATA[p])) {
                if (rawRegion.includes(c)) {
                    prov = p;
                    city = c;
                    // Try to match district
                    for (let d of ADDRESS_DATA[p][c]) {
                        if (rawRegion.includes(d)) {
                            dist = d;
                            break;
                        }
                    }
                    break;
                }
            }
        }
        
        if (prov && city) {
            return {
                region: `${prov}-${city}-${dist || '其他'}`,
                detail: detail
            };
        }
    }
    
    return {
        region: "",
        detail: fullAddress
    };
}

// ─── 9. Form Submission & Save ────────────────────────────────────────────────
addressForm.addEventListener("submit", (e) => {
    e.preventDefault();
    
    const name = receiverNameInput.value.trim();
    const phone = receiverPhoneInput.value.trim();
    const region = regionText.textContent;
    const detail = detailAddressInput.value.trim();
    
    // Validations
    if (!name) {
        showToast("请填写收货人姓名");
        return;
    }
    if (!phone || phone.length !== 11) {
        showToast("请输入11位有效的手机号");
        return;
    }
    if (region === "点击选择地址" || !region) {
        showToast("请点击选择省市区地址");
        return;
    }
    if (!detail) {
        showToast("请输入详细的街道门牌号信息");
        return;
    }
    
    // Create Saved Data object
    const savedAddress = {
        name,
        phone,
        region,
        detail,
        isDefault: isDefaultAddress
    };
    
    console.log("Saved Address Data:", savedAddress);
    
    // Show success dialog/toast
    showToast("地址保存成功！");
    
    // Reset form after saving (optional, for demo)
    /*
    setTimeout(() => {
        addressForm.reset();
        regionText.textContent = "点击选择地址";
        regionText.classList.remove("selected");
        currentProvince = "";
        currentCity = "";
        currentDistrict = "";
        isDefaultAddress = false;
        defaultCheckbox.classList.remove("checked");
    }, 1500);
    */
});
