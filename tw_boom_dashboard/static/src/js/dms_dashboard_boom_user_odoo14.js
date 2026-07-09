odoo.define('dms_boom.DashboardBoomUser', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const Dialog = require('web.Dialog')
    const core = require('web.core');

    const DashboardBoomUser = AbstractAction.extend({
        hasControlPanel: true,
        template: 'DashboardBoomUser',
        jsLibs: [
            '/web/static/lib/Chart/Chart.js',
            '/dms_boom/static/src/plugins/chartjs-plugin-datalabels.min.js',
        ],
        events: {
            'click button.btn.btn-boom-detail': 'onClickDetailButton',
            'click a#birthday-text': 'onClickDetailBirthDay',
            'click .notification-icon': 'onNotificationClick',
            'click .btn-confirm': 'onConfirmButtonClick'
        },
        _generateDetailData: function (payload) {
            let list = '', content = '';
            if (payload.status == 0) {
                content += `<h2>${payload.message}</h2>`;
            } else {
                console.log(payload)
                payload.data.forEach(rec => {
                    let badge = 'badge badge-danger';
                    if (['overdue', 'H+1'].includes(rec.status)) {
                        badge = 'badge badge-warning';
                    } else if (['current', 'Current'].includes(rec.status)) {
                        badge = 'badge badge-success';
                    }
                    list += `
                        <tr> 
                            <td>${rec.categ}</td>
                            <td><span class="${badge}">${rec.status}</span></td>
                            <td>${rec.value}</td>
                        </tr>
                    `;
                });
                content = `
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Task Name</th>
                                    <th>State</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>${list}</tbody>
                        </table>
                    </div>
                `;
            }
            return content;
        },
        // Additional function to create custom gauge chart using Chart.js
        addtext: function (t) {
            if (t.config.options.elements.center) {
                var e = t.chart.ctx, i = t.config.options.elements.center, a = i.fontStyle || "Arial", r = i.text, n = i.color || "#000", o = i.maxFontSize || 75; i.sidePadding, t.innerRadius; e.font = "30px " + a;
                var h = e.measureText(r).width, l = t.innerRadius, s = l / h, u = Math.floor(30 * s), c = 2 * t.innerRadius, g = Math.min(u, c, o), d = i.minFontSize, f = i.lineHeight || 25, x = !1; void 0 === d && (d = 20), d && g < d && (g = d, x = !0), e.textAlign = "center", e.textBaseline = "middle"; var m = (t.chartArea.left + t.chartArea.right) / 2, v = t.chartArea.top / 2 + t.chartArea.bottom - 39; if (e.font = g + "px " + a, e.fillStyle = n, !x) return void e.fillText(r, m, v);
                for (var C = r.split(" "), y = "", p = [], A = 0; A < C.length; A++) {
                    var R = y + C[A] + " "; e.measureText(R).width > l && A > 0 ? (p.push(y), y = C[A] + " ") : y = R
                }
                v -= p.length / 2 * f; for (A = 0; A < p.length; A++)e.fillText(p[A], m, v), v += f; e.fillText(y, m, v)
            }
        },
        format_rupiah: function (amount) {
            if (!amount) {
                amount = '0'
            }
            let str_amount = amount.toString()
            let rupiah = "Rp. "
            let ribuan = []
            while (str_amount) {
                ribuan.push(str_amount.slice(-3))
                str_amount = str_amount.slice(0, -3)
            }
            rupiah += ribuan.reverse().join(".") + ",-"
            return rupiah
        },
        calcLimits: function (t) {
            this.limits = t.chart.config.data.datasets[0].data;
            for (var e = this.limits, i = [], a = 0, r = 1, n = e.length; r < n; r++) {
                var o = Math.abs(e[r] - e[r - 1]); a += o, i.push(o)
            }
            this.doughnutData = i; var h = e[0], l = e[e.length - 1];
            this.isRevers = h > l, this.minValue = this.isRevers ? l : h, this.totalValue = a;
        },
        getAngleOfValue: function (t) {
            var e = 0, i = t - this.minValue;
            return e = i <= 0 ? 0 : i >= this.totalValue ? Math.PI : Math.PI * i / this.totalValue, this.isRevers ? Math.PI - e : e;
        },
        renderArrow: function (chart, t, e, i, a, r) {
            var n = this.getCoordOnCircle(t, e), o = { x: this.gaugeCenterX - n.x, y: this.gaugeCenterY - n.y };
            var h = chart.ctx;
            h.fillStyle = r, h.beginPath(), h.moveTo(o.x, o.y), n = this.getCoordOnCircle(i, e + a), h.lineTo(o.x + n.x, o.y + n.y), n = this.getCoordOnCircle(i, e - a), h.lineTo(o.x + n.x, o.y + n.y), h.closePath(), h.fill();
        },
        getCoordOnCircle: function (t, e) {
            return { x: t * Math.cos(e), y: t * Math.sin(e) }
        },
        updateGaugeDimensions: function (t) {
            var e = t.chart.chartArea; this.gaugeRadius = t.chart.innerRadius, this.gaugeCenterX = (e.left + e.right) / 2, this.gaugeCenterY = (e.top + e.bottom + t.chart.outerRadius) / 2, this.arrowLength = 40;
        },
        // Additional function to create custom gauge chart using Chart.js
        init: function (parent, action) {
            this._super(parent, action);
        },
        start: async function () {
            await this.welcomingMessage();
            this.birthdayCount();
            this.taskStatus();
            this.taskByKategori();
            this.missionDone();
            // this.missionProgress();
            this.boomMissionAges();
            this.boomLeaderBoard();
            this.potensiODTaskList();
            this.overdueTaskList();
            this.loadNotifications();
        },
        onClickDetailButton: async function (event) {
            event.preventDefault();
            let self = this;
            let id = event.target.id;
            let content = '';
            switch (id) {
                case 'detail-mission-progress':
                    await this._rpc({
                        model: 'dms.boom.task',
                        method: 'action_detail_task_status'
                    }).then(response => {
                        content = this._generateDetailData(response);
                    });
                    break;
                case 'detail-mission-ages':
                    await this._rpc({
                        model: 'dms.boom.task',
                        method: 'action_detail_boom_mission_ages'
                    }).then(response => {
                        content = this._generateDetailData(response);
                    });
                    break;
            }

            if (content) {
                let self = this;
                new Dialog(self, {
                    size: 'medium',
                    title: 'Detail',
                    $content: content
                }).open();
            }
        },
        onClickDetailBirthDay: async function (event) {
            event.preventDefault();
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_welcome_text'
            }).then((response) => {
                let birthday = response.data[1];
                let tbody = '';
                birthday.other_birthday.forEach(b => {
                    tbody += `
                        <tr>
                            <td>${b.name}</td>
                            <td>${b.branch}</td>
                            <td>${b.job}</td>
                        </tr>
                    `;
                });
                console.log(response)
                new Dialog(self, {
                    size: 'medium',
                    title: 'Born today!',
                    $content: `
                        <div class="table-responsive">
                            <table class="table table-hover table-striped">
                                <thead>
                                    <th>Name</th>
                                    <th>Branch</th>
                                    <th>Job</th>
                                </thead>
                                <tbody>${tbody}</tbody>
                            </table>
                        </div>
                    `
                }).open();

            });
        },
        welcomingMessage: function () {
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_welcome_text'
            }).then((response) => {
                let container = document.querySelector('#welcoming-text');
                let user_container = document.querySelector('#user-text');
                let quote_today = document.querySelector('#quote-today');
                let rec = response.data[0];
                let birthday = response.data[1];

                container.innerHTML = `
                    <h2>Selamat <span style="color: red">${rec.greet}</span>!! ${rec.message}</h2>
                `;
                let user = rec.name;
                if (rec.job) {
                    user += ` (${rec.job})`;
                }
                user_container.innerHTML = `
                    <h3>${user}</h3>
                `;

                if (rec.quotes) {
                    let quoteElement = document.createElement('div');
                    quoteElement.className = 'quote-load';
                    quoteElement.classList.add('truncated');
                    quoteElement.innerHTML = `
                        <b>"${rec.quotes}"</b>
                    `;
        
                    quote_today.appendChild(quoteElement);
        
                    if (quoteElement.scrollHeight > quoteElement.clientHeight) {
                        let readMoreElement = document.createElement('span');
                        readMoreElement.classList.add('read-more');
                        readMoreElement.innerText = 'Read More';
                        quote_today.appendChild(readMoreElement);
        
                        readMoreElement.addEventListener('click', () => {
                            if (quoteElement.classList.contains('truncated')) {
                                quoteElement.classList.remove('truncated');
                                readMoreElement.innerText = 'Read Less';
                            } else {
                                quoteElement.classList.add('truncated');
                                readMoreElement.innerText = 'Read More';
                            }
                        });
                    }
        
                    let authorElement = document.createElement('div');
                    authorElement.className = 'quote-author';
                    authorElement.innerHTML = `
                        <b>~ ${rec.author}</b>
                    `;
                    quote_today.appendChild(authorElement);
                }

                if (birthday.birthday == true) {
                    let title = `Happy Birthday ${rec.name}`
                    let message = ''
                    birthday.notified.forEach((n, idx) => {
                        if (idx == birthday.notified.length - 1) {
                            message += ` and ${n[0]}`
                        } else {
                            message += `, ${n[0]}`
                        }
                    });
                    if (message.length > 0) {
                        message = `You ${message} are shared the <span class="text-danger">same birthday!</span>`
                    }

                    new Dialog(self, {
                        size: 'medium',
                        title: title,
                        $content: `
                            <div style="height: 150px; width: 100%; text-align:center">
                                <img src="dms_boom/static/src/img/undraw_happy_birthday_re_c16u.svg" style="height:150px" />
                                <br/><br/>
                                <h3>${message}</h3>
                            </div>
                        `
                    }).open();
                } else if (birthday.notified.length > 0) {
                    let title = `Birthday Notification`
                    let message = ''
                    birthday.notified.forEach((n, idx) => {
                        if (idx == birthday.notified.length - 1) {
                            message += ` and ${n[0]}`
                        } else if (idx == 0) {
                            message += `${n[0]}`
                        } else {
                            message += `, ${n[0]}`
                        }
                    });
                    if (message.length > 0) {
                        if (birthday.notified.length > 1)
                            message = `collegues <span class="text-danger">${message}</span> have`
                        else
                            message = `collegue <span class="text-danger">${message}</span> has`

                        message = `Your ${message} a birthday today!`
                    }
                    new Dialog(self, {
                        size: 'medium',
                        title: title,
                        $content: `
                            <div style="height: 150px; width: 100%; text-align:center">
                                <img src="dms_boom/static/src/img/undraw_birthday_cake_re_bsw5.svg" style="height:150px" />
                                <br/><br/>
                                <h3>${message}</h3>
                            </div>
                        `
                    }).open();

                }
            });
        },
        taskStatus: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_task_status'
            }).then(function (response) {
                $('#boom-task-status-today').text(response['today']);
                $('#boom-task-status-now').text(response['now']);
                $('#boom-task-status-od').text(response['overdue']);
                $('#boom-task-status-curr').text(response['current']);
                $('#boom-task-status-pod').text(response['potensi_od']);

                $('#boom-task-status-od-today').text(response['overdue_today']);
                $('#boom-task-status-od-now').text(response['overdue_now']);

                if (response['today'] !== response['now']) {
                    $('#boom-card-today').addClass('gray-overlay');
                } else {
                    $('#boom-card-today').removeClass('gray-overlay');
                }
            });
        },
        taskByKategori: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_task_by_kategori'
            }).then(function (response) {
                let fragment = document.createDocumentFragment();
                let header = document.createElement('tr');
                header.innerHTML = `
                    <th>Kategori</th>
                    <th>Overdue</th>
                    <th>Potensi OD</th>
                `;
                document.querySelector('#boom-task-by-kategori thead').appendChild(header);
                
                let overdueSorted = [...response].sort((a, b) => b.kat_overdue - a.kat_overdue);
                let currentSorted = [...response].sort((a, b) => b.kat_current - a.kat_current);
                let potensiODSorted = [...response].sort((a, b) => b.kat_potensi_od - a.kat_potensi_od);

                response.forEach(function (el) {
                    if (el.kat_overdue != 0 || el.kat_current != 0) {
                        let row = document.createElement('tr');
                        let overdueClass = overdueSorted.indexOf(el) < 3 ? 'top-3-overdue' : '';
                        let currentClass = currentSorted.indexOf(el) < 3 ? 'top-3-current' : '';
                        let potensiODClass = potensiODSorted.indexOf(el) < 3 ? 'top-3-potensi-od' : '';

                        row.innerHTML = `
                            <td style="font-weight: bold;font-size: 13px;">${el.kategori_name}</td>
                            <td class="${overdueClass}" style="font-size: 15px;color:#EA4035;">${el.kat_overdue}</td>
                            <td class="${potensiODClass}" style="font-size: 15px;color:#fcba03">${el.kat_potensi_od}</td>
                        `;
                        fragment.appendChild(row);
                    }
                });
                document.querySelector('#boom-task-by-kategori tbody').appendChild(fragment);
                $('#boom-task-by-kategori').DataTable({
                    'scrollY': '350px',
                    'scrollCollapse': true,
                    'searching': false,
                    'lengthChange': false,
                    'paging': false,  
                    'info': false,
                    'order': [[1, 'desc'], [2, 'desc']],
                    'drawCallback': function (settings) { $("#boom-task-by-kategori thead").show() },
                });
            });
        },
        missionDone: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_mission_done'
            }).then(function (response) {
                let done = response['done'];
                let today = response['today']; 
                let textPosition = 0;

                let donePercent = today > 0 ? (done / today) * 100 : 0;

                $('#mission-done-progress-bar').css('width', donePercent.toFixed(2) + '%');

                let progressBarWidth = $('#mission-done-progress-bar').width(); 
                textPosition = 106 - (progressBarWidth / $('#mission-done-progress-bar').parent().width()) * 100;
                if (textPosition >= 74) {
                    textPosition = 74
                }
                $('#mission-done-progress-text').css('right', textPosition + '%').text(donePercent.toFixed(2) + '%');

                $('#boom-mission-done-done').text(done);
                $('#boom-mission-done-today').text(today);
                $('#boom-mission-done-od').text(response['done_overdue']);
                $('#boom-mission-done-curr').text(response['done_current']);
            });
        },

        birthdayCount: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_welcome_text'
            }).then(function (response) {
                try {
                    let birthday = response.data?.[1];
                    let length = birthday?.other_birthday?.length || 0;
                    $('#birthday-count').text('(' + length + ')');
                } catch (err) {
                    console.error('Data parsing error:', err);
                    $('#birthday-count').text('(0)');
                }
            });
        },
        
        // missionProgress: function () {
        //     let self = this;
        //     this._rpc({
        //         model: 'dms.boom.task',
        //         method: 'action_mission_progress'
        //     }).then(function (response) {
        //         document.querySelector('#boom-mission-progress').innerHTML = '';
        //         let text = `${response.value ? response.value : 0}%`;
        //         let color = '#EA4035';
        //         if (response.value > 60) {
        //             color = '#2AC990'
        //         } else if (response.value > 10) {
        //             color = '#F2BF42';
        //         }

        //         let config = {
        //             type: 'doughnut',
        //             plugins: [{
        //                 afterDraw(chart) {
        //                     let needle = chart.chart.config.options.needle;
        //                     if (needle.show) {
        
        //                         self.calcLimits(chart);
        //                         self.updateGaugeDimensions(chart);
        //                         //debugger
        //                         let needleValue = chart.chart.config.data.datasets[0].needleValue;
        
        //                         let angle = self.getAngleOfValue(needleValue);
        //                         chart.ctx.globalCompositeOperation = "source-over";
        
        //                         let arrowAngle = 33 * Math.PI / 180;
        //                         //debugger
        //                         self.renderArrow(
        //                             chart,
        //                             self.gaugeRadius + 15,
        //                             angle,
        //                             self.arrowLength - 20,
        //                             arrowAngle,
        //                             '#444'
        //                         );
        
        //                         self.addtext(chart);
        //                     }
        //                 }
        //             }],
        //             data: {
        //                 labels: [
        //                     "Initialization",
        //                     "Development",
        //                     "Completion"
        //                 ],
        //                 datasets: [{
        //                     data: [10, 40, 60],
        //                     needleValue: response.value ? response.value / 100 * 60 : 0,
        //                     backgroundColor: ["#EA4035", "#F2BF42", "#2AC990"],
        //                     hoverBackgroundColor: ["#EA4035", "#F2BF42", "#2AC990"]
        //                 }]
        //             },
        //             options: {
        //                 legend: {
        //                     display: false
        //                 },
        //                 rotation: Math.PI,
        //                 circumference: Math.PI,
        //                 elements: {
        //                     center: {
        //                         text: text,
        //                         color: color, // Default is #000000
        //                         fontStyle: 'Arial', // Default is Arial
        //                         sidePadding: 39, // Default is 20 (as a percentage)
        //                         minFontSize: 25, // Default is 20 (in px), set to false and text will not wrap.
        //                         lineHeight: 25 // Default is 25 (in px), used for when text wraps
        //                     }
        //                 },
        //                 needle: {
        //                     show: true
        //                 }
        //             }
        //         };
        
        //         let ctx = document.getElementById('boom-mission-progress');
        //         new Chart(ctx.getContext('2d'), config);
        //     });
        // },
        boomMissionAges: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_boom_mission_ages'
            }).then(function (response) {
                let value_current = response['curr'] > 0 ? response['curr'] : 0;
                let value_potensi_od = response['potensi_od'] > 0 ? response['potensi_od'] : 0;
                let value_overdue = response['overdue'] > 0 ? response['overdue'] : 0;
                document.querySelector('#boom-mission-ages').innerHTML = '';
                let canvas = document.getElementById('boom-mission-ages');
                
                let total = value_overdue + value_potensi_od + value_current;
                let totalContainer = document.getElementById('boom-mission-ages-total');
                if (totalContainer) {
                    totalContainer.innerText = 'Total Data: ' + total;
                }
                
                canvas.width = 400; 
                canvas.height = 566; 
                const ctx = canvas.getContext('2d');

                new Chart(ctx, {
                    type: 'bar',
                    plugins: [ChartDataLabels],
                    data: {
                        datasets: [{
                            data: [value_overdue, value_potensi_od, value_current, value_overdue + 15],
                            backgroundColor: ["#EA4035", "#F2BF42", "#2AC990"]
                        }],
                        labels: ["Overdue", "Potensi OD", "Current"],
                    },
                    options: {
                        legend: {
                            display: false
                        },
                        layout:{
                            padding: {
                                top: 25,
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                            xAxes: [{
                                gridLines: {
                                    color: "rgba(0, 0, 0, 0)",
                                }
                            }],
                            yAxes: [{
                                gridLines: {
                                    color: "rgba(0, 0, 0, 0)",
                                }   
                            }]
                        },
                        plugins: {
                            datalabels: {
                                anchor: 'end',
                                font: {
                                    size: 14,
                                    weight: 'bold',
                                },
                                align: 'top',
                                offset: 4
                            }
                        }
                    },
                });
            });
        },
        boomLeaderBoard: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_boom_leader_board'
            }).then(function (response) {
                let fragment = document.createDocumentFragment();
                let no = 1;
                response.forEach(function (el) {
                    let row = document.createElement('tr');
                    row.innerHTML = `
                        <tr>
                            <th>${no}</th>
                            <th><img class="img-thumbnail" style="max-height: 30px" src="${el.img_path}"/></th>
                            <th>${el.name}</th>
                            <th>${el.point}</th>
                        </tr>
                    `;
                    no += 1;
                    fragment.appendChild(row);
                });
                document.querySelector('#boom-leader-board tbody').appendChild(fragment);
                $('#boom-leader-board').DataTable({
                    'scrollY': '375px',
                    'scrollCollapse': true,
                    'searching': true,
                    'lengthChange': false,
                    'paging': false,  
                    'info': false,
                    'drawCallback': function (settings) { $("#boom-leader-board thead").remove() },
                });
            });
        },
        potensiODTaskList: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_potensi_od_task_list'
            }).then(function (response) {
                let frag = document.createDocumentFragment();
                let header = document.createElement('tr');
                header.innerHTML = `
                <th>PIC</th>
                <th>Kategori</th>
                <th>Amount</th>
                <th>Cek Detail</th>
                `;
                document.querySelector('#potensi-od-task-list thead').appendChild(header);
                response.forEach(function (el) {
                    if (el.state == 'Potensi OD') {
                        let row = document.createElement('tr');
                        let textColor = 'potensi-od-color';
                        let url = el.base_url;
                        if (el.transaction_id && el.model_name) {
                            let transaction_id = el.transaction_id
                            let model_name = el.model_name
                            url += `/web#id=${transaction_id}&view_type=form&model=${model_name}`;
                        }
                        if (el.qty) {
                            el.qty = self.format_rupiah(el.qty)
                        }
    
                        row.innerHTML = `
                            <td class="${textColor}" align="center">${el.employee_name ? el.employee_name : ''}</td>
                            <td class="${textColor}" align="center">${el.misi ? el.misi : ''}</td>
                            <td class="${textColor}" align="center">${el.qty ? el.qty : 0}</td>
                            <td class="${textColor}" align="center">
                                <button type="button" 
                                        class="btn btn-boom-detail-mission"
                                        data-url="${url}"
                                        data-model="${el.model_name}"
                                        data-id="${el.transaction_id}"
                                        data-employeeNIP="${odoo.session_info.uid}"
                                        style="border-radius: 8px;">Detail</button>
                            </td>
                        `;
                        frag.appendChild(row);
                    }
                });
                document.querySelector('#potensi-od-task-list tbody').appendChild(frag);
                $('#potensi-od-task-list').DataTable({
                    'scrollY': '250px',
                    'scrollX': false,
                    'scrollCollapse': true,
                    'searching': true,
                    'lengthChange': false,
                    'paging': false,  
                    'info': false,
                    'drawCallback': function (settings) { $("#potensi-od-task-list thead").show() },
                    'dom': '<"potensi-od-task-filter"f>rt<"bottom"ip><"clear">'
                });

                const style = document.createElement('style');
                style.innerHTML = `
                    .potensi-od-task-filter {
                        margin-right: 15px; 
                    }
                    .potensi-od-task-filter input[type="search"] {
                       padding-left: 25px;
                    }
                `;
                document.head.appendChild(style);
                document.querySelectorAll('.btn-boom-detail-mission').forEach(btn => {
                    btn.addEventListener('click', function (e) {
                        e.preventDefault();
                        let targetUrl = this.getAttribute('data-url');
                        let modelName = this.getAttribute('data-model');
                        let recordId = this.getAttribute('data-id');
                        let employeeNip = this.getAttribute('data-employeeNIP');
                
                        // Call backend to check access first
                        self._rpc({
                            route: '/boom/check_access',   // this is your custom route
                            params: { 
                                model: modelName,
                                record_id: recordId,
                                employee_nip: employeeNip 
                            }
                        }).then(function (result) {
                            if (result && result.has_access) {
                                window.open(targetUrl, '_blank');
                            } else {
                                self.displayNotification({
                                    type: 'warning',
                                    title: 'Akses Ditolak! Anda tidak memiliki akses ke data ini.',
                                    message: result && result.message ? result.message : 'Anda tidak memiliki akses ke data ini.'
                                });
                            }
                        }).catch(function (error) {
                            self.displayNotification({
                                type: 'danger',
                                title: 'Terjadi Kesalahan',
                                message: 'Gagal melakukan pengecekan akses.'
                            });
                            console.error(error);
                        });
                    });
                });
            });
        },
        overdueTaskList: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'action_overdue_task_list'
            }).then(function (response) {
                let frag = document.createDocumentFragment();
                let header = document.createElement('tr');
                header.innerHTML = `
                        <th>PIC</th>
                        <th>Kategori</th>
                        <th>Amount</th>
                        <th>Cek Detail</th>
                `;
                document.querySelector('#overdue-task-list thead').appendChild(header);
                response.forEach(function (el) {
                    if (el.state == 'Overdue') {
                        let row = document.createElement('tr');
                        let textColor = 'text-danger';
                        let url = el.base_url;
                        if (el.transaction_id && el.model_name) {
                            let transaction_id = el.transaction_id
                            let model_name = el.model_name
                            url += `/web#id=${transaction_id}&view_type=form&model=${model_name}`;
                        }
                        if (el.qty) {
                            el.qty = self.format_rupiah(el.qty)
                        }
    
                        row.innerHTML = `
                            <td class="${textColor}" align="center">${el.employee_name ? el.employee_name : ''}</td>
                            <td class="${textColor}" align="center">${el.misi ? el.misi : ''}</td>
                            <td class="${textColor}" align="center">${el.qty ? el.qty : 0}</td>
                            <td class="${textColor}" align="center">
                                <button type="button" 
                                        class="btn btn-boom-detail-mission"
                                        data-url="${url}"
                                        data-model="${el.model_name}"
                                        data-id="${el.transaction_id}"
                                        data-user_id="${odoo.session_info.uid}"
                                        style="border-radius: 8px;">Detail</button>
                            </td>
                        `;
                        frag.appendChild(row);
                    }
                });
                document.querySelector('#overdue-task-list tbody').appendChild(frag);
                $('#overdue-task-list').DataTable({
                    'scrollY': '250px',
                    'scrollX': false,
                    'scrollCollapse': true,
                    'searching': true,
                    'lengthChange': false,
                    'paging': false,  
                    'info': false,
                    'drawCallback': function (settings) { $("overdue-task-list thead").show() },
                    'dom': '<"overdue-task-list-filter"f>rt<"bottom"ip><"clear">'
                });

                const style = document.createElement('style');
                style.innerHTML = `
                    .overdue-task-list-filter {
                        margin-right: 15px; 
                    }
                    .overdue-task-list-filter input[type="search"] {
                       padding-left: 25px;
                    }
                `;
                document.head.appendChild(style);
                document.querySelectorAll('.btn-boom-detail-mission').forEach(btn => {
                    btn.addEventListener('click', function (e) {
                        e.preventDefault();
                        let targetUrl = this.getAttribute('data-url');
                        let modelName = this.getAttribute('data-model');
                        let recordId = this.getAttribute('data-id');
                        let user_id = this.getAttribute('data-user_id');
                
                        // Call backend to check access first
                        self._rpc({
                            route: '/boom/check_access',   // this is your custom route
                            params: { 
                                model: modelName,
                                record_id: recordId,
                                user_id: user_id 
                            }
                        }).then(function (result) {
                            if (result && result.has_access) {
                                window.open(targetUrl, '_blank');
                            } else {
                                self.displayNotification({
                                    type: 'warning',
                                    title: 'Akses Ditolak! Anda tidak memiliki akses ke data ini.',
                                    message: result && result.message ? result.message : 'Anda tidak memiliki akses ke data ini.'
                                });
                            }
                        }).catch(function (error) {
                            self.displayNotification({
                                type: 'danger',
                                title: 'Terjadi Kesalahan',
                                message: 'Gagal melakukan pengecekan akses.'
                            });
                            console.error(error);
                        });
                    });
                });
            });
        },
        updateNotificationCount: function (count) {
            document.getElementById('notification-count').textContent = count;
        },
        
        loadNotifications: function () {
            let self = this;
            this._rpc({
                model: 'dms.boom.task',
                method: 'get_notifications'
            }).then(function (response) {
                self.tasks = response;
                self.updateNotificationCount(response.length);
                self.renderNotificationTable(response);
            }).catch(function (error) {
                console.error('Error loading notifications:', error);
            });
        },
        renderNotificationTable: function (response) {
            let self = this;
            let frag = document.createDocumentFragment();
            let header = document.createElement('tr');
            header.innerHTML = `
                    <th>Kategori</th>
                    <th>Umur</th>
                    <th>Amount</th>
                    <th>Cek Action</th>
            `;
            document.querySelector('#notification-table thead').appendChild(header);
            if ($.fn.DataTable.isDataTable('#notification-table')) {
                $('#notification-table').DataTable().clear().destroy();
            }
            response.forEach(function (el) {
                let row = document.createElement('tr');
                let kateg_cust_name = el.misi + ' - ' + el.customer_name;
                let mission_age = el.mission_age;
                let textColor = mission_age > 1 ? 'text-danger' : 'text-success';
                if (el.qty) {
                    el.qty = self.format_rupiah(el.qty)
                }

                row.innerHTML = `
                    <td class="${textColor}" align="center">${kateg_cust_name ? kateg_cust_name : ''}</td>
                    <td class="${textColor}" align="center">${mission_age ? mission_age : ''} hari</td>
                    <td class="${textColor}" align="center">${el.qty ? el.qty : 0}</td>
                    <td align="center"><button type="button" class="btn btn-submit btn-confirm" data-task_id="${el.task_id}" style="border-radius: 20px;">Submit</button></td>
                `;
                frag.appendChild(row);
            });
            document.querySelector('#notification-table tbody').appendChild(frag);
            $('#notification-table').DataTable({
                'scrollY': '250px',
                'scrollX': false,
                'scrollCollapse': true,
                'searching': false,
                'lengthChange': false,
                'paging': false,  
                'info': false,
                'drawCallback': function (settings) { $("notification-table  thead").show() }
            });
        }, 
        onNotificationClick: function () {
            this.toggleNotificationDetails();
        },
        toggleNotificationDetails: function () {
            let notificationDetails = document.getElementById('notification-details');
            if (notificationDetails.style.display === 'none') {
                this.loadNotifications();
                notificationDetails.style.display = 'block'; // Show the details
            } else {
                notificationDetails.style.display = 'none'; // Hide the details
            }
        },
        onConfirmButtonClick: function (event) {
            const taskId = event.currentTarget.dataset.task_id;
            const task = this.tasks.find(t => t.task_id.toString() === taskId);
            this.showConfirmationDialog(task);
        },

        showConfirmationDialog: function (task) {
            const self = this;

            document.getElementById('tanggal-sales-order').textContent = `: ${task.tgl_transaksi}`;
            document.getElementById('customer-name').textContent = `: ${task.customer_name}`;
            if (task.finco) {
                document.getElementById('finco').innerHTML = `: ${task.finco}`;
                document.getElementById('finco-row').style.display = 'table-row';  // Ensure the row is visible
            } else {
                document.getElementById('finco-row').style.display = 'none';  // Hide the row if there's no finco data
            }
            document.getElementById('vehicle-type').textContent = `: ${task.tipe_kendaraan}`;
            document.getElementById('color').textContent = `: ${task.warna_kendaraan}`;
            document.getElementById('engine-number').textContent = `: ${task.no_mesin}`;
            document.getElementById('nominal-amount').textContent = `: ${task.qty}`;

            // Displaying the dialog
            document.getElementById('dialog-confirm').style.display = 'block';

            // Confirmation button handler
            document.getElementById('custom-confirm-btn').onclick = function () {
                self.confirmTransaction(task.task_id);
                self.hideConfirmationDialog();
            };

            // Close button handler
            document.querySelector('.dialog-confirm-close').onclick = function () {
                self.hideConfirmationDialog();
            };

            // Close the dialog if the user clicks outside of it
            window.onclick = function (event) {
                if (event.target == document.getElementById('dialog-confirm')) {
                    self.hideConfirmationDialog();
                }
            };
        },

        hideConfirmationDialog: function () {
            // Hide Confirmation
            document.getElementById('dialog-confirm').style.display = 'none';
        },

        confirmTransaction: function (taskId) {
            this._rpc({
                model: 'dms.boom.task',
                method: 'confirm_transaction',
                args: [taskId]
            }).then(function (result) {
                // Handle the result of the confirmation
                console.log('Transaction confirmed:', result);
                // Reload notifications after confirmation
                this.loadNotifications();
            }.bind(this)).catch(function (error) {
                console.error('Error confirming transaction:', error);
            });
        },
    });

    core.action_registry.add('dms_dashboard_boom_user', DashboardBoomUser);

    return DashboardBoomUser;

});