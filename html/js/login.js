'use strict';
const cookiematcher = /[Tt]=(?<t>[^;]+)\.(?<id>[0-9]+)(;)?/;
const cookies = document.cookie;
const token = cookiematcher.exec(cookies);
const t = token.groups.t;
localStorage.setItem("token", t);
location.href = "/dash/select";
