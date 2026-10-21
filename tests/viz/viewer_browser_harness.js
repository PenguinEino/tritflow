// Deterministic DOM, clock and Colab queue for the production viewer script.
let clock = 0, timerId = 0;
const timers = new Map(), calls = [], draws = [];
const performance = {now: () => clock};
function setTimeout(fn, delay) {
  const id = ++timerId; timers.set(id, {at:clock + delay, fn}); return id;
}
function clearTimeout(id) { timers.delete(id); }
function nextTimer() {
  return Array.from(timers, ([id, t]) => ({id, at:t.at})).sort((a,b) => a.at-b.at)[0];
}
function runTimer(id) {
  const t = timers.get(id); timers.delete(id); clock = t.at; t.fn();
}
function element() {
  return {style:{}, dataset:{}, handlers:{}, textContent:'',
    addEventListener(name, fn) { this.handlers[name] = fn; },
    setAttribute() {}, focus() {}, setPointerCapture() {},
    getBoundingClientRect() { return {left:0, top:0, width:700, height:490}; }};
}
const elements = {};
const fakeRoot = element(); fakeRoot.isConnected = true;
fakeRoot.querySelector = selector => elements[selector];
const fakeViewport = element();
fakeViewport.clientWidth = 700; fakeViewport.clientHeight = 490;
fakeViewport.insertBefore = () => {};
const fakeOverview = element();
fakeOverview.complete = true; fakeOverview.naturalWidth = 1400; fakeOverview.naturalHeight = 980;
elements['[data-role="viewport"]'] = fakeViewport;
elements['[data-gds-overview]'] = fakeOverview;
for (const name of ['status', 'scale', 'extent', 'coords']) elements['[data-role="'+name+'"]'] = element();
for (const name of ['fit', 'in', 'out']) elements['[data-action="'+name+'"]'] = element();
const document = {currentScript:{parentElement:fakeRoot}, createElement() {
  const el = element(); el.width = 0; el.height = 0;
  el.getContext = () => ({fillRect() {}, drawImage(...args) { draws.push(args.slice(1)); }});
  return el;
}};
const window = {devicePixelRatio:1, google:{colab:{kernel:{invokeFunction(name, args) {
  return new Promise((resolve, reject) => calls.push({name, args, resolve, reject, at:clock}));
}}}}};
class Image {
  constructor() { this.complete = true; this.naturalWidth = 700; }
  decode() { return Promise.resolve(); }
}
class ResizeObserver { constructor(fn) { this.fn = fn; } observe() {} }
const config = {box:[0,0,2000,1400], callback:'test.gds', background:'#000000',
  width:700, height:490, maxEdge:2048, maxPixels:2000000};
function reply(index, fail = false) {
  const call = calls[index];
  if (fail) { call.reject(new Error('temporarily disconnected')); return; }
  call.resolve({data:{'application/json':{
    image:'data:image/webp;base64,fixture', box:call.args[0],
    width:call.args[1], height:call.args[2]
  }}});
}
function event(name, values = {}) {
  canvas.handlers[name]({preventDefault() {}, button:0, pointerId:1, clientX:350, clientY:245, ...values});
}
