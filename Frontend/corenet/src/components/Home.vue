
<template>
  <div class="hello">
    <b-container>
    <b-row align-h="around">
      <b-col md="*" order="1">
        <b-card
          header="Recent Critical Events"
          class="text-center card-settings h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
          <b-card-text class="text-left">
            <ul class="list-group" >
              <li>
              <div class="list-group-item description borderless corner left font-weight-bold">Date</div>
              <div class="list-group-item description borderless corner right font-weight-bold">Event Name</div>
              </li>
              <li v-if="recentEvents.length == 0" class="list-group-item description borderless2 corner left">No Critical Events found.</li>
              <li v-for="(events, index) in recentEvents" :key="`events-${index}`">
                  <div class="list-group-item description borderless corner left">{{ convertIsoDate(events.time) }}</div>
                  <div class="list-group-item description borderless corner right">{{ events.name }}</div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
      </b-col>
      <b-col md="*" order="2">
        <b-card
          header="Last 100 events summary"
          class="text-center card-settings card h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
        <canvas id="recent-chart"></canvas>
        </b-card>
      </b-col>
    </b-row>
    <div class="bottom-pad"></div>
    <b-row align-h="around">
      <b-col md="*" order="3">
        <b-card
          header="Last 10 Executions"
          class="text-center card-settings h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
          <b-card-text class="text-left">
            <ul class="list-group" >
              <li>
              <div class="list-group-item description borderless corner left font-weight-bold">Execution Name</div>
              <div class="list-group-item description borderless corner right font-weight-bold text-right">Status</div>
              </li>
              <li v-if="recentExecutions.length == 0" class="list-group-item description borderless2 corner left">No Executions found.</li>
              <li v-for="(executions, index) in recentExecutions" :key="`events-${index}`">
                <div class="list-group-item description borderless corner left text-left">{{ executions.name }}</div>
                <div class="list-group-item description borderless corner right text-right">
                    <div v-if="executions.status === 'Completed'" style="color: green;"> {{ executions.status }} </div>
                    <div v-else style="color: red;"> {{ executions.status }} </div>
                </div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
      </b-col>
      <b-col md="*" order="4">
        <b-card
          header="Device Health"
          class="text-center card-settings card h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
          <b-card-text class="text-left">
            <ul class="list-group">
              <li>
              <div class="list-group-item description borderless corner left font-weight-bold">Device Name</div>
              <div class="list-group-item description borderless corner right font-weight-bold text-right">Health</div>
              </li>
              <li v-for="(status, name) in deviceStatus" :key="`events-${name}`">
                  <div class="list-group-item description borderless corner left text-left">{{ name }}</div>
                  <div class="list-group-item description borderless corner right text-right">
                    <div v-if="status === 'Healthy'" style="color: green;"> {{ status }} </div>
                    <div v-else-if="status === 'Unhealthy'" style="color: red;"> {{ status }} </div>
                  </div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
        </b-col>
    </b-row>
    </b-container>
    <div class="bottom-pad"></div>
  </div>
</template>

<script>
import Chart from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import { host } from '../variable.js'
import axios from 'axios'

export default {
  extends: Doughnut,
  mounted () {
    // this.createChart('recent-chart', this.chartdata)
  },
  data () {
    return {
      pagename: 'Home',
      recentEvents: [],
      deviceStatus: {},
      recentExecutions: [],
      chartdata: {
        datacollection: {
          labels: ['Information', 'Warning', 'Critical', 'Unknown'],
          datasets: [
            {
              data: [],
              backgroundColor: ['#99cc33', '#EEC200', '#cc3300']
            }
          ]
        },
        chartOptions: {
          responsive: true,
          maintainAspectRatio: false
        }
      }
    }
  },
  created () {
    this.start()
  },
  methods: {
    createChart: function (chartID, chartData) {
      const ctx = document.getElementById(chartID)
      const myChart = new Chart(ctx, {
        type: 'doughnut',
        data: chartData.datacollection,
        options: chartData.chartOptions
      })
      return myChart
    },
    getCriticalEvents: function () {
      const link = host
      const apiLink = link + 'get_events_last_critical'

      axios
        .get(apiLink)
        .then(response => {
          this.recentEvents = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    getExecutions: function () {
      const link = host
      const apiLink = link + 'get_executions_last10'

      axios
        .get(apiLink)
        .then(response => {
          this.recentExecutions = response.data
        })
        .catch(error => {
          console.log(error)
        })
    },
    getEvents: function () {
      const link = host
      const apiLink = link + 'get_events_last'

      var informationCount = 0
      var warningCount = 0
      var criticalCount = 0
      var unknownCount = 0
      axios
        .get(apiLink)
        .then(response => {
          var data = response.data
          for (var i = 0; i < data.length; i++) {
            if (data[i].priority === 'information') {
              informationCount++
            } else if (data[i].priority === 'warning') {
              warningCount++
            } else if (data[i].priority === 'critical') {
              criticalCount++
            } else {
              unknownCount++
            }
          }
          var dataset = []
          dataset.push(informationCount)
          dataset.push(warningCount)
          dataset.push(criticalCount)
          dataset.push(unknownCount)

          this.chartdata.datacollection.datasets[0].data = dataset
          this.createChart('recent-chart', this.chartdata)
          return data
        })
        .catch(error => {
          console.log(error)
        })
    },
    checkDeviceHealth: function () {
      const link = host
      const apiLink = link + 'get_events_last'

      var deviceList = {
        'P1': 'Healthy',
        'P2': 'Healthy',
        'P3': 'Healthy',
        'PE1': 'Healthy',
        'PE2': 'Healthy',
        'PE3': 'Healthy',
        'PE4': 'Healthy'
      }
      axios
        .get(apiLink)
        .then(response => {
          var data = response.data
          for (var i = 0; i < data.length; i++) {
            if (data[i].priority === 'critical') {
              var eventList = data[i].name.split('.')
              var deviceName = eventList[eventList.length - 1]

              if (deviceName in deviceList) {
                deviceList[deviceName] = 'Unhealthy'
              }
            }
          }
          this.deviceStatus = deviceList
        })
        .catch(error => {
          console.log(error)
        })
    },
    convertIsoDate: function (isodate) {
      let date = new Date(isodate)
      let year = date.getFullYear()
      let month = date.getMonth() + 1
      let dt = date.getDate()
      let hour = date.getHours()
      let minutes = date.getMinutes()
      let seconds = date.getSeconds()

      if (dt < 10) {
        dt = '0' + dt
      }
      if (month < 10) {
        month = '0' + month
      }
      if (hour < 10) {
        hour = '0' + hour
      }
      if (minutes < 10) {
        minutes = '0' + minutes
      }
      if (seconds < 10) {
        seconds = '0' + seconds
      }

      let output = dt + '/' + month + '/' + year + ' ' + hour + ':' + minutes + ':' + seconds
      return output
    },
    updateDashboard: function () {
      this.getCriticalEvents()
      this.getExecutions()
      this.getEvents()
      this.checkDeviceHealth()
      console.log('Dashboard updated')
    },
    start: function () {
      this.updateDashboard()
      setInterval(this.updateDashboard, 30000)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.row.flexRow {
    display: flex;
    flex-wrap: wrap;
}
.row.flexRow > [class*='col-'] {
    display: flex;
    flex-direction: column;
}
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  font-size: 0;
  padding: 0;
  line-height: 10px;
}
li {
  display: inline-block;
  font-size: 16px;
}
a {
  color: #42b983;
}
.description {
    width: 50%
}
.details {
  color: #000000;
}
.bottom-pad {
  margin-bottom: 50px
}
.card-settings{
  color: black;
  background-color: white;
}
.borderless {
  border-top: 1px solid black;
  border-bottom: 0 none;
  border-left: 0 none;
  border-right: 0 none;
}
.borderless2 {
  border-top: 0 none;
  border-bottom: 0 none;
  border-left: 0 none;
  border-right: 0 none;
}
.card {
  min-width: 500px;
  min-height: 400px;
  height: auto;
}
.left {
    float: left;
}

.right {
    float: right;
}
.corner {
  border-radius: 0 !important;
}
</style>
