
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
            <ul class="list-group list-group-flush" >
              <li v-for="(events, index) in recentEvents" :key="`events-${index}`">
                  <div class="list-group-item description borderless left">{{ convertIsoDate(events.time) }}</div>
                  <div class="list-group-item description borderless right">{{ events.name }}</div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
      </b-col>
      <b-col md="*" order="2">
        <b-card
          header="Device Status"
          class="text-center card-settings card h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
          <b-card-text class="text-left">
            <ul class="list-group list-group-flush borderless" >
              <li v-for="(device, index) in deviceStatus" :key="`events-${index}`">
                  <div class="list-group-item description borderless left">{{ device.name }}</div>
                  <div class="list-group-item description borderless right">{{ device.status }}</div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
        </b-col>
    </b-row>
    <div class="bottom-pad"></div>
    <b-row align-h="around">
      <b-col md="*" order="3">
        <b-card
          header="Recent Executions"
          class="text-center card-settings h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
          <b-card-text class="text-left">
            <ul class="list-group list-group-flush" >
              <li v-for="(executions, index) in recentExecutions" :key="`events-${index}`">
                <div class="list-group-item description left text-left">{{ executions.name }}</div>
                <div class="list-group-item description right text-right">{{ executions.status }}</div>
              </li>
            </ul>
          </b-card-text>
        </b-card>
      </b-col>
      <b-col md="*" order="4">
        <b-card
          header="Last 60s of events"
          class="text-center card-settings card h-100"
          header-text-variant="white"
          border-variant="dark"
          header-bg-variant="dark"
        >
        <canvas id="recent-chart"></canvas>
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
    this.createChart('recent-chart', this.chartdata)
  },
  data () {
    return {
      pagename: 'Home',
      recentEvents: [],
      deviceStatus: [
        {'name': 'P1', 'status': 'Unhealthy'},
        {'name': 'P2', 'status': 'Healthy'},
        {'name': 'P3', 'status': 'Healthy'},
        {'name': 'PE1', 'status': 'Unhealthy'},
        {'name': 'PE2', 'status': 'Healthy'}
      ],
      recentExecutions: [
        {'name': 'P1 BGP Down', 'status': 'Completed'},
        {'name': 'P2 Interface Down', 'status': 'Error'}
      ],
      lastEvents: [
        {'test': '1'}
      ],
      chartdata: {
        datacollection: {
          labels: ['Information', 'Warning', 'Critical'],
          datasets: [
            {
              data: [10, 5, 1],
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
    }
  },
  created () {
    this.getCriticalEvents()
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
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
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
</style>
