//取得cookie  
function getCookie(name) {  
	var nameEQ = name + "=";  
	var ca = document.cookie.split(';');    //把cookie分割成组  
	for(var i=0;i < ca.length;i++) {  
			var c = ca[i];                      //取得字符串  
			while (c.charAt(0)==' ') {          //判断一下字符串有没有前导空格  
				c = c.substring(1,c.length);      //有的话，从第二位开始取  
			}  
		if (c.indexOf(nameEQ) == 0) {       //如果含有我们要的name  
			return unescape(c.substring(nameEQ.length,c.length));    //解码并截取我们要值  
		}  
	}  
	return false;  
}  
//清除cookie  
function clearCookie(name) {  
	setCookie(name, "", -1);  
}  
//设置cookie  
function setCookie(name, value, seconds) {  
	seconds = seconds || 0;   //seconds有值就直接赋值，没有为0，这个根php不一样。  
	var expires = "";  
	if (seconds != 0 ) {      //设置cookie生存时间  
		var date = new Date();  
		date.setTime(date.getTime()+(seconds*1000));  
		expires = "; expires="+date.toGMTString();  
	}  
	document.cookie = name+"="+escape(value)+expires+"; path=/";   //转码并赋值  
}
function set_url_search(adds, removes) {
	var search = location.search,
		old = {};
	if (search.indexOf('?') != -1) {
		var a = search.substr(1).split('&');
		for (var i = 0; i < a.length; i++) {
			var b = a[i].indexOf('=');
			if (b > 0) {
				var c = a[i].substr(0, b),
					d = a[i].substr(b + 1);
				old[c] = d;
			}
		}
	}
	if (removes) {
		for (var i = 0; i < removes.length; i++) {
			delete old[removes[i]];
		}
	}
	for (var i in adds) {
		old[i] = encodeURIComponent(adds[i]);
	}
	search = [];
	for (var i in old) {
		search.push(i + '=' + old[i]);
	}
	location.search = '?' + search.join('&');
}
function oddsUpDown(op) {
	return op === 0 ? '' : (' style="color:' + (op > 0 ? '#FF0000' : '#009900') + '"');
}
function jtUpDown(op){
	return op === 0 ? '' : (op > 0 ? '↑' : '↓');
}

function hideTrailingChars(name, id) {
	// var oddsCompanyMap = {
	// 	'1': '官方',
	// 	'3': '36*',
	// 	'280': '皇*',
	// 	'293': '威***',
	// 	'9': '易**',
	// 	'5': '澳*',
	// 	'16': '10*',
	// 	'2': '立*',
	// 	'8': 'SN**',
	// 	'6': '韦*',
	// 	'4': 'Inter*',
	// 	'502': '12*',
	// 	'651': '利*',
	// 	'863': '18*',
	// 	'537': '盈*',
	// 	'140': '明*',
	// 	'1259': '1x*',
	// 	'15': 'Euro*',
	// 	'122': '马*',
	// 	'1120': 'Fun**',
	// 	'1055': '平*'
	// };
	// if (oddsCompanyMap[id]) return oddsCompanyMap[id]
	// if (name === '竞彩官方') return '官方';
	// var length = name.length;
	// if (length <= 1) {
	// 		return name;
	// }
	// var visibleChars = (length === 2) ? 1 : 2; // 长度=2时显示1个，>2时显示2个
	// var hiddenPart = '*'.repeat(length - visibleChars);
	// return name.substring(0, visibleChars) + hiddenPart;
	return name;
}


$(function(){
	//初盘是否显示
	$("#op_chupan").click(function(){		
		var v = $(this).attr("checked"),
			exp = new Date();
		if (v){
			$(".td_show_cp").show();
		}else{
			$(".td_show_cp").hide();
		}
		exp.setTime(exp.getTime() - 1);
		setCookie("op_chupan", (v?1:0), 0);
	});	
	//是否显示国家
	$("#guojia").click(function(){
		if ($(this).attr("checked")){
			$("#table_cont .guojia").show();
			$("#table_cont .quancheng").hide();
		}else{
			$("#table_cont .guojia").hide();
			$("#table_cont .quancheng").show();
		}
	});
	//彩种选择	
	$('#lot').find("li").live("click", function(){
		set_url_search({
			'lot':$(this).attr("val")
		}, ['order','cids']);
	});
	var chart_supported = !!(window.SvgChart && SvgChart.supported),
		chartW = 500, chartH = 300,
		colors = ["#f30", "#3a0", "#03f"],
		chartLayer = $('#tip_oz_chart'),
		chartCon = chartLayer.find('div.datachart_table'),
		useChart = false,
		options = {
			width: chartW,
			height: chartH,
			container: chartCon[0],
			lineCount: 3,
			lineColors: colors,
			lineNames: ["胜", "平", "负"],
			legendWidth: 60,
			tipsWidth: 120,
			tipsHeight: 100,
			tipsTpl: [
				'<tspan x="8" font-size="12px" fill="#666">{$time}</tspan>',
				'<tspan x="8" dy="16" fill="' + colors[0] + '">胜</tspan><tspan> : </tspan><tspan font-weight="bold">{$win}</tspan><tspan> </tspan><tspan fill="{$cwin}" font-weight="bold" font-size="13px">{$twin}</tspan>',
				'<tspan x="8" dy="16" fill="' + colors[1] + '">平</tspan><tspan> : </tspan><tspan font-weight="bold">{$draw}</tspan><tspan> </tspan><tspan fill="{$cdraw}" font-weight="bold" font-size="13px">{$tdraw}</tspan>',
				'<tspan x="8" dy="16" fill="' + colors[2] + '">负</tspan><tspan> : </tspan><tspan font-weight="bold">{$lost}</tspan><tspan> </tspan><tspan fill="{$clost}" font-weight="bold" font-size="13px">{$tlost}</tspan>',
				'<tspan x="8" dy="16">返还率</tspan><tspan> : </tspan><tspan font-size="11px">{$ret}</tspan>'
			].join(""),
			tipsCb: function(time, self, prev){
				function trend(i) {
					var diff = prev && (self[i] - prev[i]);
					return prev ? (diff > 0 ? 0 : (diff < 0 ? 1 : 2)) : 2;
				}
				function color(i) {
					return ["red", "green", "inherit"][trend(i)];
				}
				function arrow(i) {
					return ["\u2191", "\u2193", ""][trend(i)];
				}
				return {
					time: php_date("n月j日 H:i", time),
					win: parseFloat(self[0]).toFixed(2),
					cwin: color(0),
					twin: arrow(0),
					draw: parseFloat(self[1]).toFixed(2),
					cdraw: color(1),
					tdraw: arrow(1),
					lost: parseFloat(self[2]).toFixed(2),
					clost: color(2),
					tlost: arrow(2),
					"ret": parseFloat((100 / (1 / self[0] + 1 / self[1] + 1 / self[2]))).toFixed(2) + "%"
				}
			}
	};
	//弹层
	window.OZ = {
		layer: $('#tip_oz').add('#tip_kl'),
		r: function(li, i) {
			li = $(li);
			i = i ? 1 : 0;
			var s = location.search,
				p = location.pathname,
				m = s.match(/[\?&]id=(\d+)/),
				f = (m ? m[1] : p.match(/\/(rangqiu|ouzhi)-(\d+)/)[2]),
				tr = li.closest("tr[id]"),
				data = {
					fid: f,
					cid: tr.attr('cid'),
					r: /[\?&]r=-1/.test(s) || /-r--1/.test(p) ? -1 : 1,
					time: tr.attr('data-time'),
					handicapline:tr.attr('handicapline'),
					type: ['rspf', 'kelly'][i]
				};
			if (chart_supported && i == 0) {
				chartCon.html('<p style="text-align:center">正在加载中...</p>');
			}
			$.ajax({
				url: '../fenxi1/json/rspf.php',
				data: data,
				dataType: 'json',
				cache: false,
				success: function(d) {
                    if(d &&  d.code && d.code == -100){
                        window.location.href = window.location.protocol +"//passport.500.com/user/login/?backurl=" + encodeURIComponent(window.location.href)
                    }
					var showChart = !!(chartLayer && chartLayer.is(":visible"));
					OZ.layer.hide();
					chartLayer.hide();
					if (d) {
						var p = li.offset(),
							tb = OZ.tbody.eq(i),
							ly = OZ.layer.eq(i),
							trs = [],
							row, last,
							pos = {
								top: p.top + 20,
								left: p.left + ((i || /yazhi|daxiao/.test(location.pathname)) ? -160 : 25)
							};
						if (chart_supported && i == 0) {
							chartCon.html('');
							var data = [];
							for (var j = d.length - 1; j >= 0; -- j) {
								var a = d[j];
								if (a[0] > 0) {
									data.push({
										time: new Date(a[4].replace(/-/g, "/")).getTime(),
										values: a.slice(0, 3)
									});
								}
							}
							if (data.length) {
								var chart = SvgChart.factory(options);
								chart.setData(data);
								chart.render();
							} else {
								chartCon.html('<p style="text-align:center">暂无数据</p>');
							}
							chartLayer.css(pos);
							chartLayer.toggle(useChart);
							ly.toggle(!useChart);
						} else {
							ly.show();
						}
						for (var j = d.length - 1; j >= 0; --j) {
							row = d[j];
							trs.unshift(['<tr>', '<td', oddsUpDown(last ? row[0] - last[0] : 0), '>', parseFloat(row[0]).toFixed(2), jtUpDown(last ? row[0] - last[0] : 0), '</td>', '<td', oddsUpDown(last ? row[1] - last[1] : 0), '>', parseFloat(row[1]).toFixed(2), jtUpDown(last ? row[1] - last[1] : 0), '</td>', '<td', oddsUpDown(last ? row[2] - last[2] : 0), '>', parseFloat(row[2]).toFixed(2), jtUpDown(last ? row[2] - last[2] : 0), '</td>', i ? '' : '<td>' + parseFloat(row[3]).toFixed(2) + '%</td>', '<td>', row[i ? 3 : 4].replace(/^\d+-(.+):\d+$/, '$1'), '</td>', '</tr>'].join(''));
							last = row;
						}
						tb.html(trs.join(''));
						ly.css(pos);
						var ht = ly.find("table")[0].offsetHeight;
						if (ht > 210) {
							ly.find('div.datachart_table').find("table").width(417);
							ly.find('div.datachart_table').height(210);
						}else if (ht > 0){
							ly.find('div.datachart_table').height(ht);
							ly.find('div.datachart_table').find("table").width(434);
						}
						//ly.find('div.datachart_table').height(d.length > 9 ? 279 : d.length * 28 + 27);
					}
				}
			});
		}
	};
	OZ.tbody = OZ.layer.find('tbody');
	OZ.layer.find('a.tips_close').click(function() {
		OZ.layer.hide();
	});
	chartLayer.find('a.tips_close').click(function() {
		chartLayer.hide();
	});
	if (chart_supported) {
		var ozLayer = OZ.layer.eq(0);
		var ozTitle = ozLayer.find("a.tit_cur");
		ozTitle.click(function(){
			useChart = true;
			ozLayer.hide();
			chartLayer.show();
		});
		var chartTitle = chartLayer.find("a.tit_cur");
		chartTitle.click(function(){
			useChart = false;
			chartLayer.hide();
			ozLayer.show();
		});
	}else{
		var ozLayer = OZ.layer.eq(0);
		var ozTitle = ozLayer.find("a.tit_cur");
		ozTitle.hide();
	}
});

(function() {
	//定制功能
	if (/[\?&]from=[^&]+/.test(location.search)) {
		return;
	}
	var CUSTOMIZE_KEY = 'odds_customize',
		ordernum = 0,
		CUSTOMIZE_DATA;

	function in_array(v, a, b) {
		for (var i = 0; i < a.length; i++) {
			if (b ? (v === a[i]) : (v == a[i])) {
				return i;
			}
		}
		return -1;
	}
	function center(o) {
		return {
			top: $(document).scrollTop() + ~~ ((document.documentElement.clientHeight - o.height()) / 2),
			left: $(document).scrollLeft() + ~~ ((document.documentElement.clientWidth - o.width()) / 2)
		};
	}
	function trim(s) {
		if (s){
			return s.replace(/^\s+/, '').replace(/\s+$/, '');
		}else{
			return '';
		}
	}
	function drag(panel, layer) {
		var ex, ey, tx, ty, state = false;

		function mousedown(e) {
			if (panel[0].setCapture) {
				panel[0].setCapture();
			} else {
				$(document).mousemove(mousemove);
				$(document).mouseup(mouseup);
			}
			e = e || window.event;
			eX = e.clientX;
			eY = e.clientY;
			tX = ~~layer.css('left').replace('px', '');
			tY = ~~layer.css('top').replace('px', '');
			panel.css('cursor', 'move');
			e.returnValue = false;
			if (e.preventDefault) {
				e.preventDefault();
			}
			state = true;
		}
		function mouseup(e) {
			state = false;
			panel.css('cursor', 'auto');
			if (panel[0].releaseCapture) {
				panel[0].releaseCapture();
			} else {
				$(document).unbind('mousemove', mousemove);
				$(document).unbind('mouseup', mouseup);
			}
		}
		function mousemove(e) {
			if (state) {
				e = e || window.event;
				layer.css('left', e.clientX - eX + tX);
				layer.css('top', e.clientY - eY + tY);
			}
		}
		panel.mousedown(mousedown);
		panel.mousemove(mousemove);
		panel.mouseup(mouseup);
	}
	$(function() {
		if (/[\?&]order=[^&]+/.test(location.search) || /[\?&]cids=[^&]+/.test(location.search)) {
			(function() {
				if (window.odds_stat) {
					odds_stat();
				} else {
					setTimeout(arguments.callee, 100);
				}
			})();
		}
		var down = $('#customize_down'),
			up = $('#customize_up'),
			tip = $('#customize_tip'),
			layer = $('#customize_layer'),
			list = $('#customize_list'),
			_select = $('#pltype').add('#spfselect'),
			cmp_new = $('#customize_new'),
			cmp_ul = $('#company_ul'),
			chk_ul = $('#check_ul'),
			csm_cids = [],
			csm_typeshow = $('#typeshow'),
			csm_select = $('#choose'),
			csm_name = $('#customize_name'),
			csm_save = $('#customize_save'),
			loading_layer = $('#loading_layer');
		drag(layer.find('div.tips_title'), layer);
		function load2() {
			csm_select.find('li:gt(3)').remove();
			if (/ck_user=[^=;]+/.test(document.cookie)) {
				$.ajax({
					url: '/fenxi1/customize/get_customize.php',
					cache: false,
					dataType: 'json',
					success: function(d) {
						var s = location.search;
						var o = s.match(/[\?&]order=(\d+)/);
						for (var i = 0; i < d.length; i++) {
							if (d[i].companies.length) {
								if (o&&o[1]==i){
									csm_typeshow.attr("val", (5+i));
									csm_typeshow.text(d[i].name);
								}
								var option = $('<li val="'+(5+i)+'">' + d[i].name + '</li>');
								csm_select.append(option);
							}
						}
					}
				});
			} else {
				var d = richStorage.get(CUSTOMIZE_KEY);
				if (d) {
					for (var i = 0; i < d.length; i++) {
						if (d[i].companies.length) {
							if (/[\?&]cids=[^&]+/.test(location.search)){
								csm_typeshow.attr("val", (5+i));
								csm_typeshow.text(d[i].name);
							}
							var option = $('<li val="'+(5+i)+'">' + d[i].name + '</li>');
							csm_select.append(option);
						}
					}
				}
			}
		}
		load2();

		function load(d) {
			CUSTOMIZE_DATA = d;
			var li = [];
			for (var i = 0; i < d.length; i++) {
				li.push('<li><a href="javascript:void(0)" class="btn_blue_l btn_blue_l_h24 btn_width_auto' + (i ? '' : ' btn_blue_cur') + '">' + d[i].name + '(' + d[i].companies.length + ')</a></li>');
			}
			list.html(li.join(''));
			var a = $('a', list);
			a.each(function(i) {
				var t = $(this);
				t.click(function() {
					var d = CUSTOMIZE_DATA;
					a.removeClass('btn_blue_cur');
					t.addClass('btn_blue_cur').html(d[i].name + '(' + d[i].companies.length + ')');
					csm_cids = [];
					chk_ul.html('');
					var cmps = d[i].companies;
					for (var j = 0; j < cmps.length; j++) {
						$("a[cid='" + cmps[j] + "']", cmp_ul).click();
					}
					ordernum = i;
					csm_name.val(d[i].name);
				});
			});
			a.eq(0).click();
			load2();
		}
		$('#customize_close').click(function() {
			_select.css('visibility', 'visible');
			$('#customize_layer').hide();
			$('#mask_layer').hide();
		});
		//选择公司
		csm_select.find("li").live("click", function(){
			$("#typeshow").attr("val", $(this).attr("val"));
			$("#typeshow").text($(this).text());
			var v = $(this).attr("val");
			if (v<5){
				set_url_search({
					'ctype': v
				}, ['order', 'cids']);
			}else{
				if (/ck_user=[^=;]+/.test(document.cookie)) {
					set_url_search({
						'order': v-5
					}, ['ctype', 'cids']);
				}else{
					var CUSTOMIZE_KEY = 'odds_customize',
						d = richStorage.get(CUSTOMIZE_KEY),
						v = [],
						i = ~~v;
					for (var j = 0; j < d[i].companies.length; j++) {
						v.push(d[i].companies[j]);
					}
					set_url_search({
						'cids': v.join(',')
					}, ['ctype', 'order']);
				}
			}
		})
		//定制弹层
		cmp_new.click(function() {
			_select.css('visibility', 'hidden');
			up.click();
			$('#mask_layer').show();
			layer.show();
			layer.css(center(layer));
			var o = layer.offset();
			loading_layer.css({
				'top': o.top,
				'left': o.left,
				'width': layer.width(),
				'height': layer.height()
			}).show();
			$.ajax({
				url: '/fenxi1/customize/get_company.php',
				dataType: 'json',
				cache: true,
				success: function(a) {
					loading_layer.hide();
					var li = [];
					if (!a || !a.length) {
						return;
					}
					for (var i = 0; i < a.length; i++) {
						li.push('<li><a href="javascript:void(0)" cid="' + a[i][0] + '" firstchar="' + a[i][1].charAt(0).toLowerCase() + '" ismain="' + (a[i][2] == 1 ? 1 : 0) + '">' + hideTrailingChars(a[i][1], a[i][0]) + (a[i][2] == 1 ? ' <img src="/images/oz_zhu.gif" alt="" />' : '') + '</a></li>');
					}
					cmp_ul.html(li.join(''));
					$('a', cmp_ul).click(function() {
						var max = /ck_user=[^=;]+/.test(document.cookie) ? 30 : 10;
						if (csm_cids.length >= max) {
							alert('您最多选择' + max + '家公司');
							return;
						}
						var t = $(this),
							cid = ~~t.attr('cid');
						if (in_array(cid, csm_cids) == -1) {
							csm_cids.push(cid);
							var li = $('<li cid="' + cid + '" cname="' + trim(t.text()) + '">' + t.html() + '<a href="javascript:void(0)" class="del">删除</a></li>');
							chk_ul.append(li);
							var a = $('a', li).click(function() {
								li.remove();
								csm_cids.splice(in_array(cid, csm_cids), 1);
							});
							li.hover(function() {
								li.css('background', '#E8EEF8');
								a.css('background-position', '-115px -51px')
							}, function() {
								li.css('background', '#FFFFFF');
								a.css('background-position', '-115px -35px')
							});
						}
					});
					if (/ck_user=[^=;]+/.test(document.cookie)) {
						$.ajax({
							url: '/fenxi1/customize/get_customize.php',
							cache: false,
							dataType: 'json',
							success: function(d) {
								load(d);
								csm_save.unbind().click(function() {
									var v = csm_name.val();
									if (!/^[a-zA-Z0-9_]{1,10}$/.test(v.replace(/[\u4e00-\u9fa5]/g, 'aa'))) {
										alert('请输入5个以内中文字符或10个以内字母、数字');
										return;
									}
									csm_save.attr('disabled', 'disabled');
									csm_save.val('保存中');
									var data = [{
										name: 'customizename',
										value: v
									}, {
										name: 'ordernum',
										value: ordernum
									}],
										cmps = [];
									$('li', chk_ul).each(function() {
										var t = $(this);
										data.push({
											name: 'companyids[]',
											value: ~~t.attr('cid')
										});
										cmps.push(t.attr('cid'));
									});
									$.ajax({
										url: '/fenxi1/customize/set_customize.php',
										dataType: 'json',
										type: 'post',
										data: data,
										timeout: 1e4,
										success: function(d) {
											if (d) {
												alert('保存成功');
												CUSTOMIZE_DATA[ordernum] = {
													name: v,
													companies: cmps
												};
												$('a', list).eq(ordernum).click();
												load2();
											} else {
												alert('对不起，保存失败，请检查您的输入信息');
											}
										},
										error: function() {
											alert('对不起，保存超时，请检查您的输入信息');
										},
										complete: function() {
											csm_save.val('保 存');
											csm_save.removeAttr('disabled');
										}
									})
								});
							}
						});
					} else {
						if (!richStorage.get(CUSTOMIZE_KEY)) {
							richStorage.set(CUSTOMIZE_KEY, [{
								name: '我的定制一',
								companies: []
							}]);
						}
						load(richStorage.get(CUSTOMIZE_KEY));
						csm_save.unbind().click(function() {
							var v = csm_name.val();
							if (!/^[a-zA-Z0-9]{1,10}$/.test(v.replace(/[\u4e00-\u9fa5]/g, 'aa'))) {
								alert('请输入5个以内中文字符或10个以内字母、数字');
								return false;
							}
							var cmps = [];
							$('li', chk_ul).each(function() {
								var t = $(this);
								cmps.push(t.attr('cid'));
							});
							richStorage.set(CUSTOMIZE_KEY, CUSTOMIZE_DATA = [{
								name: v,
								companies: cmps
							}]);
							alert('保存成功');
							load2();
							$('a.btn_blue_cur', list).click();
						});
					}
					var cmp_li = $('li', cmp_ul);
					$('#customize_filter a').each(function(i) {
						$(this).click(function() {
							cmp_li.each(function() {
								var t = $(this),
									a = t.find('a'),
									regs = [null, /[^a-z0-9]/, /[0-9]/, /[a-d]/, /[e-h]/, /[i-l]/, /[m-p]/, /[q-t]/, /[u-z]/],
									b = i ? regs[i].test(a.attr('firstchar')) : a.attr('ismain') == '1';
								t.toggle(b);
							});
						});
					});
					var cmp_search = $('#customize_search'),
						search_handle;
					cmp_search.keyup(function() {
						clearTimeout(search_handle);
						search_handle = setTimeout(function() {
							var v = cmp_search.val().toLowerCase();
							cmp_li.each(function() {
								var t = $(this),
									b = t.find('a').text().toLowerCase().indexOf(v) == 0;
								t.toggle(b);
							});
						}, 300);
					});
				}
			});
		});
	});
})();
(function(){
	"use strict";
	var _table = $("#datatb"),
		_table_style = $('#table_style').val() == '0',
		_pltype = $("#pltype"),
		ldb = new _LoadingBar();
	$("#radioleft span[class!='lab_cur'] :radio").click(function() {
		if (this.parentNode.parentNode.className != "lab_cur") {
			var v = this.value;
			set_url_search({
				'ctype': v
			}, ['order', 'cids']);
		}
	});

	function setOddOrEven() {
		var b = false;
		_table.find('tr').each(function() {
			var t = $(this),
				p = t.attr('ttl');
			if (t.css('display') != 'none' && p) {
				if (p == 'zy' || p == 'sx1') {
					b = !b;
				}
				b ? t.removeClass('tr2') : t.addClass('tr2');
			}
		});
	}
	_pltype.change(function() {
		$("#excelst").val(this.value);
		_table.hide();
		var tr = _table.find("tr:gt(1)").not($("#step_line")),
			bl = this.value == 1,
			cs, rs;
		tr.each(function(i) {
			var t = $(this);
			if (i % 2) {
				if (bl) {
					if (t.prev().is(":visible")) {
						t.show();
					}
				} else {
					t.hide();
				}
			} else {
				cs = this.cells, rs = bl ? 2 : 1;
				cs[0].setAttribute('rowSpan', rs);
				if (cs.length == 13) {
					cs[1].setAttribute('rowSpan', rs);
					cs[12].setAttribute('rowSpan', rs);
				}
			}
		});
		_table.show();
	});

	function checkLoadAll() {
		if (typeof(_notLoaded) !== 'undefined') {
			if (_notLoaded === 0) {
				_notLoaded = true;
				$('#step_line').show();
			}
			if (_notLoaded) {
				window.oddsLoadAll();
			}
		}
	}
	var _checkbox;

	function reset() {
		if (typeof(_notLoaded) === 'undefined' || _notLoaded === false) {
			_checkbox = _table.find(':checkbox');
		}(_checkbox ? _checkbox : _table.find(':checkbox')).removeAttr('checked');
	}
	//恢复默认
	$('#qx2').click(window.showOddsAll = function() {
		checkLoadAll();
		(function() {
			if (typeof(_notLoaded) !== 'undefined' && _notLoaded) {
				setTimeout(arguments.callee, 10);
			} else {
				_table.hide();
				var cks = _table.find(':checkbox');
				cks.each(function() {
					if (!this.checked) {
						var id = this.id.replace(/\D/g, '');
						$("tr#"+id).show();
						$(this).attr('checked', 'checked');
					}
				});
//				$("#dcid,#scid").val('');
				$("#nowcnum").html(typeof(_total) !== 'undefined' ? _total : cks.length);
				setOddOrEven();
				_table.show();
				reset();
			}
		})();
	});
	//显示选择
	$('#sx2').click(function() {
		checkLoadAll();
		(function() {
			if (typeof(_notLoaded) !== 'undefined' && _notLoaded) {
				setTimeout(arguments.callee, 10);
			} else {
				_table.hide();
				if (typeof(_notLoaded) !== 'undefined' && _notLoaded) {
					_notLoaded = 0;
					$('#step_line').hide();
				}
				var num = 0,
					hid = [],
					sid = [],
					cid_arr={};
				
				_table.find(':checkbox').each(function() {
					var id = this.id.replace(/\D/g, ''),
						cid = this.value;
					if ($(this).attr('checked')) {
						if(!cid_arr.hasOwnProperty(cid)){
							cid_arr[cid]=1;
							num++;
						}						
						if (typeof(_notLoaded) !== 'undefined' && _notLoaded === 0) {
							sid.push(id);
						}
						_table.find('tr.more_tr').hide();
						$("tr#"+id).show();
					} else {
						hid.push(id);
						$("tr#"+id).hide();
					}
				});
//				$("#dcid").val(hid.join(','));
//				$("#scid").val(sid.join(','));
				$("#nowcnum").html(num);
				setOddOrEven();
				reset();
				_table.show();
			}
		})();
	});
	//反选
	$('#fx2').click(function() {
		checkLoadAll();
		(function() {
			if (typeof(_notLoaded) !== 'undefined' && _notLoaded) {
				setTimeout(arguments.callee, 10);
			} else {
				_table.find('tr').each(function() {
					var tr = $(this),
						ck = tr.find(':checkbox');
					if (ck.length) {
						if (tr.css('display') != 'none' && !ck.attr('checked')) {
							ck.attr('checked', 'checked');
						} else {
							ck.removeAttr('checked');
						}
					}
				});
			}
		})();
	});
	//下载
	$(".downpl").click(function(e) {
		ldb.show();
		checkLoadAll();
		(function() {
			if (typeof(_notLoaded) !== 'undefined' && _notLoaded) {
				setTimeout(arguments.callee, 10);
			} else {
				try {
					if (e && e.stopPropagation) {
						e.stopPropagation();
					} else {
						window.event.cancelBubble = true;
					}
					if (e && e.preventDefault) {
						e.preventDefault();
					} else {
						window.event.returnValue = false;
					}
				} catch (ex) {}
				var plform = $("#plform"),
					datalist = {};
				plform.find("input:gt(0)").remove();
				$("[xls]").not(":hidden").each(function(){
					var td = [],
						td1 = [],
						in_name = $(this).attr("xls");
					datalist[in_name] = datalist[in_name] || [];
					$(this).find("[row]").each(function(){
						for (var i=0;i<$(this).attr("row");i++){
							var o = $(this),
								myV = "";
							if (o.css("display") == 'none' || o.parent().css("display") == 'none'){
								continue;
							}
							//隐藏不可见内容
							if (in_name=='row'){
								if (o.find(":hidden").length>0){
									o.find(":hidden").replaceWith("");
								}
							}
							//下拉菜单
							if (o.find("select").length>0){
								o = o.find("option:selected");
							}
							myV = o.text().replace(/[↑↓]/, '');
							//判定是否为初盘
							if (o.hasClass("td_show_cp") || o.parent().hasClass("td_show_cp")){
								if (td1.length==0){
									td1.push();
								}
								td1.push(myV);
							}else{
								td.push(myV);
							}
						}
					});
					if (td1.length>0){
						td1.unshift(td[1]);
						td1.unshift(td[0]);						
						datalist[in_name].push(td1.join("|"));
					}
					datalist[in_name].push(td.join("|"));
				});	
				var inputList = ['header', 'row'],
					n;
				for (var il=0;il<inputList.length;il++){
					n = inputList[il];
					if (datalist[n] && datalist[n].length>0){
						var input = '<input type="hidden" name="'+n+'" value="'+datalist[n].join("$")+'"/>';
						plform.append(input);
					}
				}
				plform.submit();		
				(function() {
					if (/downloadgood/.test(document.cookie)) {
						var exp = new Date();
						exp.setTime(exp.getTime() - 1);
						document.cookie = "downloadgood=0;path=/;expires=" + exp.toUTCString() + ';domain=' + location.hostname;
						ldb.hide();
					} else {
						setTimeout(arguments.callee, 100);
					}
				})();
			}
		})();
	});
})();