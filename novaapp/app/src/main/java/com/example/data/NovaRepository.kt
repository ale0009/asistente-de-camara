package com.example.data

import kotlinx.coroutines.flow.Flow
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class NovaRepository(private val db: NovaDatabase) {
    val allMissions: Flow<List<Mission>> = db.missionDao().getAllMissions()
    val recentLogs: Flow<List<ActionLogEntry>> = db.actionLogDao().getRecentLogs()
    val allNotes: Flow<List<ObsidianNote>> = db.obsidianNoteDao().getAllNotes()

    suspend fun insertMission(mission: Mission) = db.missionDao().insertMission(mission)
    suspend fun updateMission(mission: Mission) = db.missionDao().updateMission(mission)
    suspend fun deleteMission(id: Long) = db.missionDao().deleteMission(id)
    suspend fun resetAllMissions() = db.missionDao().resetAllMissions()

    suspend fun addLog(source: String, message: String, type: String = "INFO") {
        val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
        val timestampStr = sdf.format(Date())
        db.actionLogDao().insertLog(
            ActionLogEntry(
                timestamp = timestampStr,
                source = source,
                message = message,
                logType = type
            )
        )
    }

    suspend fun clearLogs() = db.actionLogDao().clearLogs()

    fun searchNotes(query: String): Flow<List<ObsidianNote>> =
        if (query.isBlank()) db.obsidianNoteDao().getAllNotes()
        else db.obsidianNoteDao().searchNotes(query)

    suspend fun insertNote(note: ObsidianNote) = db.obsidianNoteDao().insertNote(note)
    suspend fun updateNote(note: ObsidianNote) {
        if (note.isProtected) {
            throw IllegalStateException("OverwriteError: Document '${note.title}' is protected and cannot be overwritten.")
        }
        db.obsidianNoteDao().updateNote(note)
    }
}
