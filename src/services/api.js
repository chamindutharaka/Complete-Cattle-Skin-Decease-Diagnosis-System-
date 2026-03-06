import axios from "axios";

export const diagnosisAPI = axios.create({
  baseURL: "http://localhost:5007"
});

export const monitoringAPI = axios.create({
  baseURL: "http://localhost:5006"
});