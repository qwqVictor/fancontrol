# fancontrol

Dell PowerEdge assisted fan control script.

Supports Linux and VMware ESXi.  

The behavior defined by `get_thermal_level()` and `FANSPEED`. See the code.

### Notice for ESXi
For ESXi, use `init-script` and copy it to `/opt/fancontrol`.

To mitigate the ESXi background killing, you can only use SIGKILL or SIGUSR1 to end it.

### License

[Unlicense](LICENSE).

---

Code with ❤️ by [Victor Huang](https://qwq.ren).
